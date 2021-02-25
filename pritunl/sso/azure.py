from pritunl import settings
from pritunl import logger

import requests
import urllib.request, urllib.parse, urllib.error

def verify_azure(user_name):
    response = requests.post(
        'https://login.microsoftonline.com/%s/oauth2/token' % \
            settings.app.sso_azure_directory_id,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        data={
            'grant_type': 'client_credentials',
            'client_id': settings.app.sso_azure_app_id,
            'client_secret': settings.app.sso_azure_app_secret,
            'resource': 'https://graph.windows.net',
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error('Bad status from Azure api',
            'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()

    access_token = data['access_token']

    response = requests.get(
        'https://graph.windows.net/%s/users/%s' % (
            settings.app.sso_azure_directory_id,
            urllib.parse.quote(user_name),
        ),
        headers={
            'Authorization': 'Bearer %s' % access_token,
        },
        params={
            'api-version': '1.6',
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error('Bad status from Azure api',
            'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()

    if not data.get('accountEnabled'):
        logger.error('Azure account is disabled',
            'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    response = requests.get(
        'https://graph.windows.net/%s/users/%s/memberOf' % (
            settings.app.sso_azure_directory_id,
            urllib.parse.quote(user_name),
        ),
        headers={
            'Authorization': 'Bearer %s' % access_token,
        },
        params={
            'api-version': '1.6',
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error('Bad status from Azure api',
            'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()

    roles = []

    for membership in data['value']:
        if membership.get('objectType') != 'Group':
            continue
        roles.append(membership.get('displayName'))

    return True, roles
