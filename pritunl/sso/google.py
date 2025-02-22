from pritunl import settings
from pritunl import utils

import json
import io
from google.oauth2 import service_account
from googleapiclient import discovery

def verify_google(user_email):
    user_domain = user_email.split('@')[-1]

    if not isinstance(settings.app.sso_match, list):
        raise TypeError('Invalid sso match')

    if not user_domain in settings.app.sso_match:
        return False, []

    google_key = settings.app.sso_google_key
    google_email = settings.app.sso_google_email

    if not google_key or not google_email:
        return True, []

    data = json.loads(google_key)

    credentials = service_account.Credentials.from_service_account_info(
        data,
        scopes=[
            'https://www.googleapis.com/auth/admin.directory.user.readonly',
            'https://www.googleapis.com/auth/admin.directory.group.readonly',
        ],
    )

    delegated_credentials = credentials.with_subject(google_email)

    service = discovery.build(
        'admin', 'directory_v1', credentials=delegated_credentials)

    data = service.users().get(userKey=user_email).execute()
    if data.get('suspended'):
        return False, []

    results = service.groups().list(userKey=user_email,
        maxResults=settings.app.sso_google_groups_max).execute()

    groups = []
    for group in results.get('groups') or []:
        groups.append(utils.filter_unicode(group['name']))

    return True, groups
