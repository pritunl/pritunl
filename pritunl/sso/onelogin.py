from pritunl.constants import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import urllib
import httplib

def auth_onelogin(username):
    try:
        response = utils.request.post(
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
        return True
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
