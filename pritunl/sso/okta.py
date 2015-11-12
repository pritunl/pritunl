from pritunl.exceptions import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import urllib
import httplib
import time

def get_user_id(username):
    try:
        response = utils.request.get(
            OKTA_URL + '/api/v1/users/%s' % urllib.quote(username),
            headers={
                'Accept': 'application/json',
                'Authorization': 'SSWS %s' % OKTA_API_KEY,
            },
        )
    except httplib.HTTPException:
        # TODO Log here
        return None

    if response.status_code != 200:
        # TODO Log here
        return None

    data = response.json()
    if 'id' in data:
        return data['id']

    # TODO Log here
    return None

def get_factor_id(user_id):
    try:
        response = utils.request.get(
            OKTA_URL + '/api/v1/users/%s/factors' % user_id,
            headers={
                'Accept': 'application/json',
                'Authorization': 'SSWS %s' % OKTA_API_KEY,
            },
        )
    except httplib.HTTPException:
        # TODO Log here
        return None

    if response.status_code != 200:
        # TODO Log here
        return None

    not_active = False
    for factor in response.json():
        if 'id' not in factor or 'provider' not in factor or \
                'factorType' not in factor or 'status' not in factor:
            continue

        if factor['provider'].lower() != 'okta' or \
                factor['factorType'].lower() != 'push':
            continue

        if factor['status'].lower() != 'active':
            not_active = True
            continue

        return factor['id']

    if not_active:
        # TODO Log not active error
        pass
    else:
        # TODO Log not found error
        pass

    return None
