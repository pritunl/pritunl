from pritunl import settings
from pritunl import logger
from pritunl import utils

import json
import time
import random
import base64
import requests
import urllib.parse

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_DIRECTORY_URL = 'https://admin.googleapis.com/admin/directory/v1'
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
]
GOOGLE_REQUEST_TIMEOUT = 15
GOOGLE_REQUEST_ATTEMPTS = 2
GOOGLE_RETRY_STATUS_CODES = (408, 429, 500, 502, 503, 504)
GOOGLE_TOKEN_RETRY_ERRORS = (
    'internal_failure',
    'server_error',
    'temporarily_unavailable',
)
GOOGLE_DIRECTORY_RETRY_REASONS = (
    'rateLimitExceeded',
    'userRateLimitExceeded',
    'quotaExceeded',
)

def _base64url(data):
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

class _BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer %s' % self.token
        return request

def _request(method, url, retry_check, **kwargs):
    kwargs.setdefault('timeout', GOOGLE_REQUEST_TIMEOUT)

    for attempt in range(1, GOOGLE_REQUEST_ATTEMPTS):
        try:
            response = requests.request(method, url, **kwargs)
        except requests.exceptions.SSLError:
            raise
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as error:
            logger.warning('Google api request failed, retrying', 'sso',
                url=url,
                attempt=attempt,
                error=str(error),
            )
        else:
            if not retry_check(response):
                return response

            logger.warning('Bad status from Google api, retrying', 'sso',
                url=url,
                attempt=attempt,
                status_code=response.status_code,
            )
            response.close()

        time.sleep(2 ** (attempt - 1) + random.uniform(0, 0.5))

    return requests.request(method, url, **kwargs)

def _token_retry_check(response):
    if response.status_code in GOOGLE_RETRY_STATUS_CODES:
        return True

    if response.status_code != 400:
        return False

    try:
        data = response.json()
    except ValueError:
        return False

    return isinstance(data, dict) and \
        data.get('error') in GOOGLE_TOKEN_RETRY_ERRORS

def _directory_retry_check(response):
    if response.status_code in GOOGLE_RETRY_STATUS_CODES:
        return True

    if response.status_code != 403:
        return False

    try:
        errors = response.json()['error']['errors']
        return any(error.get('reason') in GOOGLE_DIRECTORY_RETRY_REASONS
            for error in errors)
    except (ValueError, KeyError, TypeError, AttributeError):
        return False

def _get_access_token(key_data, google_email):
    header = {
        'alg': 'RS256',
        'typ': 'JWT',
    }
    if key_data.get('private_key_id'):
        header['kid'] = key_data['private_key_id']

    now = int(time.time())
    payload = {
        'iss': key_data['client_email'],
        'sub': google_email,
        'aud': GOOGLE_TOKEN_URL,
        'scope': ' '.join(GOOGLE_SCOPES),
        'iat': now,
        'exp': now + 3600,
    }

    signing_input = '%s.%s' % (
        _base64url(json.dumps(header, separators=(',', ':')).encode()),
        _base64url(json.dumps(payload, separators=(',', ':')).encode()),
    )

    private_key = serialization.load_pem_private_key(
        key_data['private_key'].encode(),
        password=None,
    )
    signature = private_key.sign(
        signing_input.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    response = _request('POST', GOOGLE_TOKEN_URL, _token_retry_check,
        data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': '%s.%s' % (signing_input, _base64url(signature)),
        },
    )

    if response.status_code != 200:
        logger.error('Bad status from Google token api', 'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return None

    return response.json().get('access_token')

def verify_google(user_email, skip_user=False, skip_groups=False):
    user_domain = user_email.split('@')[-1]

    if not isinstance(settings.app.sso_match, list):
        raise TypeError('Invalid sso match')

    if not user_domain in settings.app.sso_match:
        return False, []

    google_key = settings.app.sso_google_key
    google_email = settings.app.sso_google_email

    if not google_key or not google_email or skip_user:
        return True, []

    access_token = _get_access_token(json.loads(google_key), google_email)
    if not access_token:
        return False, []

    auth = _BearerAuth(access_token)

    response = _request('GET',
        GOOGLE_DIRECTORY_URL + '/users/%s' % urllib.parse.quote(
            user_email, safe=''),
        _directory_retry_check,
        auth=auth,
    )

    if response.status_code != 200:
        logger.error('Bad status from Google directory api', 'sso',
            user_email=user_email,
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()
    if data.get('suspended'):
        return False, []

    if skip_groups:
        return True, []

    response = _request('GET', GOOGLE_DIRECTORY_URL + '/groups',
        _directory_retry_check,
        auth=auth,
        params={
            'userKey': user_email,
            'maxResults': settings.app.sso_google_groups_max,
        },
    )

    if response.status_code != 200:
        logger.error('Bad status from Google directory api', 'sso',
            user_email=user_email,
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    groups = []
    for group in response.json().get('groups') or []:
        groups.append(utils.filter_unicode(group['name']))

    return True, groups
