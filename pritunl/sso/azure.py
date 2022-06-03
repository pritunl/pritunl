from pritunl import settings
from pritunl import logger
from pritunl import utils

import requests
import time
import urllib.request, urllib.parse, urllib.error

def _verify_azure_1(user_name):
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
        roles.append(utils.filter_unicode(membership.get('displayName')))

    return True, roles

def _verify_azure_2(user_name):
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
            'resource': 'https://graph.microsoft.com',
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error('Bad status from Azure api',
            'sso',
            username=user_name,
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()

    access_token = data['access_token']

    response = requests.get(
        'https://graph.microsoft.com/v1.0/%s/users/%s' % (
            settings.app.sso_azure_directory_id,
            urllib.parse.quote(user_name),
        ),
        headers={
            'Authorization': 'Bearer %s' % access_token,
        },
        params={
            '$select': 'id,userPrincipalName,accountEnabled',
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error('Bad status from Azure api',
            'sso',
            username=user_name,
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()

    if data.get('userPrincipalName', '').lower() != user_name.lower():
        logger.error('Bad status from Azure api',
            'sso',
            username=user_name,
            azure_username=data['userPrincipalName'],
        )
        return False, []

    if not data.get('accountEnabled'):
        logger.error('Azure account is disabled',
            'sso',
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    url = 'https://graph.microsoft.com/v1.0/users/%s/memberOf' % (
        data['id'],
    )
    roles = []
    start = time.time()

    while True:
        response = requests.get(
            url,
            headers={
                'Authorization': 'Bearer %s' % access_token,
                'Content-Type': 'application/json',
            },
            json={
                'securityEnabledOnly': str(settings.app.sso_azure_security_groups_only).lower(),
            },
            timeout=20,
        )

        if response.status_code != 200:
            logger.error('Bad status from Azure api',
                'sso',
                username=user_name,
                status_code=response.status_code,
                response=response.content,
            )
            return False, []

        data = response.json()

        for group_data in data['value']:
            display_name = group_data.get('displayName')
            if not display_name:
                continue
            if settings.app.sso_azure_allow_groups and display_name.replace(" ","_").replace("'","") not in settings.app.sso_azure_allow_groups:
                continue
            roles.append(display_name)

        next_url = data.get('@odata.nextLink')
        if next_url:
            url = next_url
        else:
            break

        if time.time() - start > 45:
            logger.error('Azure group listing timed out',
                'sso',
                username=user_name,
                azure_username=data['userPrincipalName'],
            )
            return False, []

    return True, roles

def verify_azure(user_name):
    if settings.app.sso_azure_version == 1:
        return _verify_azure_1(user_name)
    return _verify_azure_2(user_name)
