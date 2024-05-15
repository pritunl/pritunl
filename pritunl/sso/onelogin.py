from pritunl.constants import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import time
import urllib.request, urllib.parse, urllib.error
import http.client
import requests
import xml.etree.ElementTree

def _get_base_url():
    return 'https://api.%s.onelogin.com' % settings.app.sso_onelogin_region

def _get_access_token():
    response = requests.post(
        _get_base_url() + '/auth/oauth2/v2/token',
        headers={
            'Authorization': 'client_id:%s, client_secret:%s' % (
                settings.app.sso_onelogin_id,
                settings.app.sso_onelogin_secret,
            ),
            'Content-Type': 'application/json',
        },
        json={
            'grant_type': 'client_credentials',
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error getting access token', 'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return None

    return response.json()['access_token']

def auth_onelogin(username):
    if not settings.app.sso_onelogin_id or \
            not settings.app.sso_onelogin_secret:
        try:
            response = requests.get(
                ONELOGIN_URL + '/api/v2/users?username=%d' % (
                    urllib.parse.quote(username)),
                auth=(settings.app.sso_onelogin_key, 'x'),
                )
        except http.client.HTTPException:
            logger.exception('OneLogin api error getting user', 'sso',
                username=username,
            )
            return False

        if response.status_code == 200:
            data = xml.etree.ElementTree.fromstring(response.content)
            if data.find('status').text == '1':
                return True

            logger.warning('OneLogin user disabled', 'sso',
                username=username,
            )
        elif response.status_code == 404:
            logger.error('OneLogin user not found', 'sso',
                username=username,
            )
        elif response.status_code == 406:
            logger.warning('OneLogin user disabled', 'sso',
                username=username,
            )
        else:
            logger.error('OneLogin api error', 'sso',
                username=username,
                status_code=response.status_code,
                response=response.content,
            )
        return False

    access_token = _get_access_token()
    if not access_token:
        return False

    response = requests.get(
        _get_base_url() + '/api/2/users?username=%s' % urllib.parse.quote(username),
        headers={
            'Authorization': 'bearer: %s' % access_token,
            'Content-Type': 'application/json',
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error getting user', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    users = response.json()
    if not users:
        logger.error('OneLogin user not found', 'sso',
            username=username,
        )
        return False

    user = users[0]
    if user['state'] != 1:
        logger.warning('OneLogin user disabled', 'sso',
            username=username,
        )
        return False

    onelogin_app_id = settings.app.sso_onelogin_app_id
    if not onelogin_app_id:
        return True

    try:
        onelogin_app_id = int(onelogin_app_id)
    except ValueError:
        pass

    user_id = user['id']

    response = requests.get(
        _get_base_url() + '/api/2/users/%d/apps' % user_id,
        headers={
            'Authorization': 'bearer: %s' % access_token,
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error getting apps', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    applications = response.json()
    if not applications:
        logger.error('OneLogin user apps not found', 'sso',
            username=username,
        )
        return False

    for application in applications:
        if application['id'] == onelogin_app_id:
            return True

    logger.warning('OneLogin user is not assigned to application', 'sso',
        username=username,
        onelogin_app_id=onelogin_app_id,
    )

    return False

def auth_onelogin_secondary(username, passcode, remote_ip, onelogin_mode):
    access_token = _get_access_token()
    
    if not access_token:
        return False

    if 'passcode' in onelogin_mode and not passcode:
        logger.error('OneLogin passcode empty', 'sso',
            username=username,
        )
        return False

    response = requests.get(
        _get_base_url() + '/api/2/users?username=%s' % urllib.parse.quote(username),
        headers={
            'Authorization': 'bearer: %s' % access_token,
            'Content-Type': 'application/json',
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error getting  users', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    users = response.json()
    if not users:
        logger.error('OneLogin user not found', 'sso',
            username=username,
        )
        return False

    user = users[0]
    if user['state'] != 1:
        logger.error('OneLogin user disabled', 'sso',
            username=username,
        )
        return False

    user_id = user['id']

    response = requests.get(
        _get_base_url() + '/api/2/mfa/users/%d/devices' % user_id,
        headers={
            'Authorization': 'bearer: %s' % access_token,
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error getting devices', 'sso',
            username=username,
            onelogin_mode=onelogin_mode,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    device_id = None
    devices = response.json()
    needs_trigger = False
    for device in devices:
        if device['auth_factor_name'] != 'OneLogin':
            continue

        if device['default']:
            device_id = device['device_id']
            needs_trigger = True
            break

    if not device_id:
        if 'none' in onelogin_mode:
            logger.info('OneLogin secondary not available, skipped', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
            )
            return True

        logger.error('OneLogin secondary not available', 'sso',
            username=username,
            onelogin_mode=onelogin_mode,
        )

        return False

    if needs_trigger or 'push' in onelogin_mode:
        response = requests.post(
            _get_base_url() + '/api/2/mfa/users/%d/verifications' % (
                user_id),
            headers={
                'Authorization': 'bearer: %s' % access_token,
                'Content-Type': 'application/json',
                'X-Forwarded-For': remote_ip,
            },
            json={
                'device_id': device_id
            },
        )

        if response.status_code != 201:
            logger.error('OneLogin api error creating verification', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
                status_code=response.status_code,
                response=response.content,
            )
            return False

        activate = response.json()['id']
        if not activate:
            logger.error('OneLogin activate empty', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
            )
            return False

    start = utils.time_now()
    while True:
        if utils.time_now() - start > 45:
            logger.error('OneLogin secondary timed out', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
                user_id=user_id,
            )
            return False

        response = requests.get(
            _get_base_url() + '/api/2/mfa/users/%d/verifications/%s' % (
                user_id, activate),
            headers={
                'Authorization': 'bearer: %s' % access_token,
                'Content-Type': 'application/json',
            },
        )

        if response.status_code != 200 and response.status_code != 401:
            logger.error('OneLogin api error activating mfa', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
                status_code=response.status_code,
                response=response.content,
            )
            return False

        verify = response.json()['status']
        if not verify:
            logger.error('OneLogin verify empty', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
            )
            return False

        if response.status_code == 200:
            if verify == "pending":
                time.sleep(0.5)
                continue
            
            if verify == "accepted":
                return True

            logger.error('OneLogin secondary rejected', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
                user_id=user_id,
            )
            return False

        if response.status_code != 200:
            logger.error('OneLogin verify bad data', 'sso',
                username=username,
                onelogin_mode=onelogin_mode,
                status_code=response.status_code,
                response=response.content,
            )
            return False

        return True