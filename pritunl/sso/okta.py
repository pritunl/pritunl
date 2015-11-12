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

def auth_okta(username, strong=False, ipaddr=None, type=None, info=None):
    user_id = get_user_id(username)
    if not user_id:
        return False

    factor_id = get_factor_id(user_id)
    if not factor_id:
        return False

    try:
        response = utils.request.post(
            OKTA_URL + '/api/v1/users/%s/factors/%s/verify' % (
                user_id, factor_id),
            headers={
                'Accept': 'application/json',
                'Authorization': 'SSWS %s' % OKTA_API_KEY,
            },
        )
    except httplib.HTTPException:
        # TODO Log here
        return False

    if response.status_code != 201:
        # TODO Log here
        return False

    poll_url = None

    while True:
        data = response.json()
        result = data.get('factorResult').lower()
        print result

        # TODO Log here
        if result == 'success':
            return True
        elif result == 'challenge':
            return False
        elif result == 'waiting':
            pass
        elif result == 'failed':
            return False
        elif result == 'cancelled':
            return False
        elif result == 'timeout':
            return False
        elif result == 'time_window_exceeded':
            return False
        elif result == 'passcode_replayed':
            return False
        elif result == 'error':
            return False
        else:
            return False

        if not poll_url:
            links = data.get('_links')
            if not links:
                return False

            poll = links.get('poll')
            if not poll:
                return False

            poll_url = poll.get('href')
            if not poll_url:
                return False

        time.sleep(0.2)

        try:
            response = utils.request.get(
                poll_url,
                headers={
                    'Accept': 'application/json',
                    'Authorization': 'SSWS %s' % OKTA_API_KEY,
                },
            )
        except httplib.HTTPException:
            # TODO Log here
            return False

        if response.status_code != 200:
            # TODO Log here
            return False
