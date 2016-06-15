from pritunl.constants import *
from pritunl import settings
from pritunl import logger

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
    if settings.app.sso_onelogin_id and settings.app.sso_onelogin_secret:
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

        return True
    else:
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
