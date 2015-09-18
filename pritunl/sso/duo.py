from pritunl.exceptions import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import base64
import email
import hmac
import hashlib
import urllib
import httplib

def sign(method, path, params):
    now = email.Utils.formatdate()
    canon = [now, method.upper(), settings.app.sso_host.lower(), path]
    args = []
    for key in sorted(params.keys()):
        val = params[key]
        if isinstance(val, unicode):
            val = val.encode("utf-8")
        args.append(
            '%s=%s' % (urllib.quote(key, '~'), urllib.quote(val, '~')))
    canon.append('&'.join(args))
    canon = '\n'.join(canon)

    sig = hmac.new(settings.app.sso_secret.encode(), canon, hashlib.sha1)
    auth = '%s:%s' % (settings.app.sso_token.encode(), sig.hexdigest())

    return {
        'Date': now,
        'Authorization': 'Basic %s' % base64.b64encode(auth),
    }

def auth_duo(username, strong=False, ipaddr=None, type=None, info=None):
    params = {
        'username': username,
        'factor': 'push',
        'device': 'auto',
    }

    if ipaddr:
        params['ipaddr'] = ipaddr

    if type:
        params['type'] = type

    if info:
        params['pushinfo'] = urllib.urlencode(info)

    headers = sign('POST', '/auth/v2/auth', params)
    url = 'https://%s/auth/v2/auth' % settings.app.sso_host

    try:
        response = utils.request.post(url,
            headers=headers,
            params=params,
            timeout=settings.app.sso_timeout,
        )
    except httplib.HTTPException:
        return False, None

    data = response.json()
    resp_data = data.get('response')
    if resp_data and resp_data.get('result') == 'allow':
        if strong and resp_data.get('status') == 'bypass':
            allow = False
        else:
            allow = True
    elif data.get('code') == 40002:
        raise InvalidUser('Invalid username')
    else:
        allow = False
        logger.error('Duo authentication failure', 'sso',
            data=data,
        )

    return allow, None
