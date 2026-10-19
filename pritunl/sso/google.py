from pritunl import settings
from pritunl import logger
from pritunl import utils

import json
import time
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

def _base64url(data):
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

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

    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': '%s.%s' % (signing_input, _base64url(signature)),
        },
        timeout=30,
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

    headers = {
        'Authorization': 'Bearer %s' % access_token,
    }

    response = requests.get(
        GOOGLE_DIRECTORY_URL + '/users/%s' % urllib.parse.quote(
            user_email, safe=''),
        headers=headers,
        timeout=30,
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

    response = requests.get(
        GOOGLE_DIRECTORY_URL + '/groups',
        headers=headers,
        params={
            'userKey': user_email,
            'maxResults': settings.app.sso_google_groups_max,
        },
        timeout=30,
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
