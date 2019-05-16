from pritunl import settings
from pritunl import logger

import json
import requests

def verify_authzero(user_name):
    response = requests.post(
        'https://%s.auth0.com/oauth/token' % settings.app.sso_authzero_domain,
        headers={
            'Content-Type': 'application/json',
        },
        data=json.dumps({
            'grant_type': 'client_credentials',
            'client_id': settings.app.sso_authzero_app_id,
            'client_secret': settings.app.sso_authzero_app_secret,
            'audience': 'https://%s.auth0.com/api/v2/' % \
                settings.app.sso_authzero_domain,
        }),
        timeout=30,
    )

    if response.status_code != 200:
        logger.error('Bad status from Auth0 api',
            'sso',
            user_name=user_name,
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()

    access_token = data['access_token']

    response = requests.get(
        'https://%s.auth0.com/api/v2/users' % (
            settings.app.sso_authzero_domain,
        ),
        headers={
            'Authorization': 'Bearer %s' % access_token,
        },
        params={
            'search_engine': 'v3',
            'email': user_name,
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error('Bad status from Auth0 api',
            'sso',
            user_name=user_name,
            status_code=response.status_code,
            response=response.content,
        )
        return False, []

    data = response.json()

    user_id = None
    roles = []
    groups = []
    for usr in data:
        if usr.get('email') != user_name:
            continue

        user_id = usr.get('user_id')

        app_metadata = usr.get('app_metadata')
        if app_metadata:
            app_authorization = app_metadata.get('authorization')
            if app_authorization:
                roles = app_authorization.get('roles')
                groups = app_authorization.get('groups')

        break

    if not user_id:
        logger.error('Failed to find Auth0 user',
            'sso',
            user_name=user_name,
        )
        return False, []

    return True, groups
