from pritunl.constants import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import urllib.request, urllib.parse, urllib.error
import http.client
import requests

def auth_jumpcloud(username):
    try:
        response = requests.get(
            JUMPCLOUD_URL +
            '/api/systemusers?filter=email:$eq:%s' % (
                urllib.parse.quote(username)),
            headers={
                'Accept': 'application/json',
                'X-Api-Key': settings.app.sso_jumpcloud_secret,
            },
        )
    except http.client.HTTPException:
        logger.exception('JumpCloud api error', 'sso',
            username=username,
        )
        return False

    if response.status_code != 200:
        logger.error('JumpCloud api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    data = response.json()

    if not data.get('totalCount') or data.get('totalCount') < 1:
        logger.warning('JumpCloud user not found', 'sso',
            username=username,
        )
        return False

    user_id = None
    for user_data in data.get('results') or []:
        if user_data.get('email') != username:
            continue

        if user_data.get('account_locked') or user_data.get('suspended') or \
                not user_data.get('activated'):
            logger.warning('JumpCloud user disabled', 'sso',
                username=username,
            )
            return False

        user_id = user_data.get('_id') or user_data.get('id')
        break

    if not user_id:
        logger.warning('JumpCloud user not found', 'sso',
            username=username,
        )
        return False

    if not settings.app.sso_jumpcloud_app_id:
        return True

    try:
        response = requests.get(
            JUMPCLOUD_URL +
            '/api/v2/users/%s/applications?limit=100' % user_id,
            headers={
                'Accept': 'application/json',
                'X-Api-Key': settings.app.sso_jumpcloud_secret,
            },
        )
    except http.client.HTTPException:
        logger.exception('JumpCloud api error', 'sso',
            username=username,
        )
        return False

    if response.status_code != 200:
        logger.error('JumpCloud api error', 'sso',
            username=username,
            status_code=response.status_code,
            response=response.content,
        )
        return False

    data = response.json()
    for app_data in data or []:
        if app_data.get('id') == settings.app.sso_jumpcloud_app_id:
            return True

    logger.warning('JumpCloud user not bound to application', 'sso',
        username=username,
    )
    return False
