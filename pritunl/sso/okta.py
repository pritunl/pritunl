from pritunl import settings
from pritunl import logger

import urllib.request, urllib.parse, urllib.error
import http.client
import time
import urllib.parse
import requests

def _getokta_url():
    parsed = urllib.parse.urlparse(settings.app.sso_saml_url)
    return '%s://%s' % (parsed.scheme, parsed.netloc)

def get_user_id(username):
    try:
        response = requests.get(
            _getokta_url() + '/api/v1/users/%s' % urllib.parse.quote(username),
            headers={
                'Accept': 'application/json',
                'Authorization': 'SSWS %s' % settings.app.sso_okta_token,
            },
        )
    except http.client.HTTPException:
        logger.exception('Okta api error', 'sso',
            username=username,
        )
        return None

    if response.status_code != 200:
        logger.error('Okta api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return None

    data = response.json()

    user_id = data.get('id')
    if not user_id:
        logger.error('Okta username not found', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return None

    if data['status'].lower() != 'active':
        logger.warning('Okta user is not active', 'sso',
            username=username,
        )
        return None

    return user_id

def auth_okta(username):
    user_id = get_user_id(username)
    if not user_id:
        return False

    okta_app_id = settings.app.sso_okta_app_id
    if not okta_app_id:
        return True

    try:
        response = requests.get(
            _getokta_url() + \
            '/api/v1/apps/%s/users/%s' % (okta_app_id, user_id),
            headers={
                'Accept': 'application/json',
                'Authorization': 'SSWS %s' % settings.app.sso_okta_token,
            },
        )
    except http.client.HTTPException:
        logger.exception('Okta api error', 'sso',
            username=username,
            okta_app_id=okta_app_id,
            user_id=user_id,
        )
        return None

    if response.status_code == 404:
        logger.warning('Okta user is not assigned to application', 'sso',
            username=username,
            okta_app_id=okta_app_id,
            user_id=user_id,
        )
        return False

    if response.status_code != 200:
        logger.error('Okta api error', 'sso',
            username=username,
            okta_app_id=okta_app_id,
            user_id=user_id,
            status_code=response.status_code,
            response=response.content,
        )
        return None

    if response.json():
        return True

    logger.warning('Okta user is not assigned to application', 'sso',
        username=username,
        okta_app_id=okta_app_id,
        user_id=user_id,
    )

    return False

def auth_okta_secondary(username, passcode, remote_ip, okta_mode):
    user_id = get_user_id(username)
    if not user_id:
        return False

    if 'passcode' in okta_mode and not passcode:
        logger.error('Okta passcode empty', 'sso',
            username=username,
            okta_user_id=user_id,
        )
        return False

    try:
        response = requests.get(
            _getokta_url() + '/api/v1/users/%s/factors' % user_id,
            headers={
                'Accept': 'application/json',
                'Authorization': 'SSWS %s' % settings.app.sso_okta_token,
            },
        )
    except http.client.HTTPException:
        logger.exception('Okta api error', 'sso',
            username=username,
            okta_user_id=user_id,
        )
        return False

    if response.status_code != 200:
        logger.error('Okta api error', 'sso',
            username=username,
            okta_user_id=user_id,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    not_active = False
    factor_id = None
    data = response.json()
    for factor in data:
        if not factor.get('id') or not factor.get('provider') or \
                not factor.get('status'):
            continue

        if factor.get('provider').lower() not in ('okta', 'google') or \
                factor.get('status').lower() != 'active':
            continue

        if 'push' in okta_mode:
            if factor['factorType'].lower() != 'push':
                continue
        elif 'passcode' in okta_mode:
            if factor['factorType'].lower() != 'token:software:totp':
                continue
        else:
            continue

        if factor_id is None or factor.get('provider').lower() == 'okta':
            factor_id = factor['id']

    if not factor_id:
        if 'none' in okta_mode:
            logger.info('Okta secondary not available, skipped', 'sso',
                username=username,
                okta_user_id=user_id,
            )
            return True
        elif not_active:
            logger.warning('Okta secondary not active', 'sso',
                username=username,
                okta_user_id=user_id,
            )
            return False
        else:
            logger.warning('Okta secondary not available', 'sso',
                username=username,
                okta_user_id=user_id,
            )
            return False

    verify_data = {}
    if passcode:
        verify_data['passCode'] = passcode

    logger.info('Sending Okta verify', 'sso',
        username=username,
        okta_user_id=user_id,
        okta_factor_id=factor_id,
    )

    try:
        response = requests.post(
            _getokta_url() + '/api/v1/users/%s/factors/%s/verify' % (
                user_id, factor_id),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'SSWS %s' % settings.app.sso_okta_token,
                'X-Forwarded-For': remote_ip,
            },
            json=verify_data,
        )
    except http.client.HTTPException:
        logger.exception('Okta api error', 'sso',
            username=username,
            user_id=user_id,
            factor_id=factor_id,
        )
        return False

    if response.status_code != 200 and response.status_code != 201:
        logger.error('Okta api error', 'sso',
            username=username,
            user_id=user_id,
            factor_id=factor_id,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    poll_url = None

    start = time.time()
    while time.time() - start < settings.app.sso_timeout:
        data = response.json()
        result = data.get('factorResult').lower()

        if result == 'success':
            return True
        elif result == 'waiting':
            pass
        else:
            logger.warning('Okta push rejected', 'sso',
                username=username,
                user_id=user_id,
                factor_id=factor_id,
                result=result,
            )
            return False

        if not poll_url:
            links = data.get('_links')
            if not links:
                logger.error('Okta cant find links', 'sso',
                    username=username,
                    user_id=user_id,
                    factor_id=factor_id,
                    data=data,
                )
                return False

            poll = links.get('poll')
            if not poll:
                logger.error('Okta cant find poll', 'sso',
                    username=username,
                    user_id=user_id,
                    factor_id=factor_id,
                    data=data,
                )
                return False

            poll_url = poll.get('href')
            if not poll_url:
                logger.error('Okta cant find href', 'sso',
                    username=username,
                    user_id=user_id,
                    factor_id=factor_id,
                    data=data,
                )
                return False

        time.sleep(settings.app.sso_okta_poll_rate)

        try:
            response = requests.get(
                poll_url,
                headers={
                    'Accept': 'application/json',
                    'Authorization': 'SSWS %s' % settings.app.sso_okta_token,
                },
            )
        except http.client.HTTPException:
            logger.exception('Okta poll api error', 'sso',
                username=username,
                user_id=user_id,
                factor_id=factor_id,
            )
            return False

        if response.status_code != 200:
            logger.error('Okta poll api error', 'sso',
                username=username,
                user_id=user_id,
                factor_id=factor_id,
                status_code=response.status_code,
                response=response.content,
            )
            return False
