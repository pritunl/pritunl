from pritunl import settings

import json
import io
import apiclient.discovery
import oauth2client.service_account

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

    credentials = oauth2client.service_account. \
        ServiceAccountCredentials.from_p12_keyfile_buffer(
        data['client_email'],
        io.StringIO(data['private_key']),
        'notasecret',
        scopes=[
            'https://www.googleapis.com/auth/admin.directory.group.readonly',
        ],
    )

    credentials = credentials.create_delegated(google_email)

    service = apiclient.discovery.build(
        'admin', 'directory_v1', credentials=credentials)

    results = service.groups().list(userKey=user_email).execute()

    groups = []
    for group in results.get('groups') or []:
        groups.append(group['name'].replace(' ', ''))

    return True, groups
