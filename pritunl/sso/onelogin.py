from pritunl.constants import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import time
import urllib
import httplib
import requests
import xml.etree.ElementTree

def _get_base_url():
    return 'https://api.%s.onelogin.com' % settings.app.sso_onelogin_region

def _get_access_token():
    response = requests.post(
        _get_base_url() + '/auth/oauth2/token',
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
        logger.error('OneLogin api error', 'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return None

    return response.json()['data'][0]['access_token']

def auth_onelogin(username):
    if not settings.app.sso_onelogin_id or \
            not settings.app.sso_onelogin_secret:
        try:
            response = requests.get(
                ONELOGIN_URL + '/api/v3/users/username/%s' % (
                    urllib.quote(username)),
                auth=(settings.app.sso_onelogin_key, 'x'),
                )
        except httplib.HTTPException:
            logger.exception('OneLogin api error', 'sso',
                username=username,
            )
            return False

        if response.status_code == 200:
            data = xml.etree.ElementTree.fromstring(response.content)
            if data.find('status').text == '1':
                return True

            logger.error('OneLogin user disabled', 'sso',
                username=username,
            )
        elif response.status_code == 404:
            logger.error('OneLogin user not found', 'sso',
                username=username,
            )
        elif response.status_code == 406:
            logger.error('OneLogin user disabled', 'sso',
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
        _get_base_url() + '/api/1/users',
        headers={
            'Authorization': 'bearer:%s' % access_token,
            'Content-Type': 'application/json',
        },
        params={
            'username': username,
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    users = response.json()['data']
    if not users:
        logger.error('OneLogin user not found', 'sso',
            username=username,
        )
        return False

    user = users[0]
    if user['status'] != 1:
        logger.error('OneLogin user disabled', 'sso',
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
        _get_base_url() + '/api/1/users/%d/apps' % user_id,
        headers={
            'Authorization': 'bearer:%s' % access_token,
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    applications = response.json()['data']
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

def auth_onelogin_push(username, strong=False, ipaddr=None,
        type=None, info=None):
    if not settings.app.sso_onelogin_push:
        return True

    access_token = _get_access_token()
    if not access_token:
        return False

    response = requests.get(
        _get_base_url() + '/api/1/users',
        headers={
            'Authorization': 'bearer:%s' % access_token,
        },
        params={
            'username': username,
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    users = response.json()['data']
    if not users:
        logger.error('OneLogin user not found', 'sso',
            username=username,
        )
        return False

    user = users[0]
    if user['status'] != 1:
        logger.error('OneLogin user disabled', 'sso',
            username=username,
        )
        return False

    user_id = user['id']

    response = requests.get(
        _get_base_url() + '/api/1/users/%d/otp_devices' % user_id,
        headers={
            'Authorization': 'bearer:%s' % access_token,
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    device_id = None
    devices = response.json()['data']['otp_devices']
    for device in devices:
        if device['auth_factor_name'] != 'OneLogin Protect':
            continue

        if device['default']:
            device_id = device['id']
            break
        elif not device_id:
            device_id = device['id']

    if not device_id:
        if settings.app.sso_onelogin_skip_unavailable:
            logger.info('OneLogin push not available, skipped', 'sso',
                username=username,
            )
            return True

        logger.error('OneLogin push not available', 'sso',
            username=username,
        )

        return False

    response = requests.post(
        _get_base_url() + '/api/1/users/%d/otp_devices/%d/trigger' % (
            user_id, device_id),
        headers={
            'Authorization': 'bearer:%s' % access_token,
            'Content-Type': 'application/json',
            'X-Forwarded-For': ipaddr,
        },
        json={
            'ipaddr': ipaddr,
        },
    )

    if response.status_code != 200:
        logger.error('OneLogin api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    activate = response.json()['data']
    if not activate:
        logger.error('OneLogin activate empty', 'sso',
            username=username,
        )
        return False

    state_token = activate[0]['state_token']

    start = utils.time_now()
    while True:
        if utils.time_now() - start > 45:
            logger.error('OneLogin push timed out', 'sso',
                username=username,
                user_id=user_id,
            )
            return False

        response = requests.post(
            _get_base_url() + '/api/1/users/%d/otp_devices/%d/verify' % (
                user_id, device_id),
            headers={
                'Authorization': 'bearer:%s' % access_token,
                'Content-Type': 'application/json',
                'X-Forwarded-For': ipaddr,
            },
            json={
                'state_token': state_token,
            },
        )

        if response.status_code != 200 and response.status_code != 401:
            logger.error('OneLogin api error', 'sso',
                username=username,
                status_code=response.status_code,
                response=response.content,
            )
            return False

        verify = response.json()['status']
        if not verify:
            logger.error('OneLogin verify empty', 'sso',
                username=username,
            )
            return False

        if response.status_code == 401:
            if 'Authentication pending' in verify['message']:
                time.sleep(0.5)
                continue

            logger.error('OneLogin push rejected', 'sso',
                username=username,
                user_id=user_id,
            )
            return False

        if response.status_code != 200 or verify['type'] != "success":
            logger.error('OneLogin verify bad data', 'sso',
                username=username,
                status_code=response.status_code,
                response=response.content,
            )
            return False

        return True
