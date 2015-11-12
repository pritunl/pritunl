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
