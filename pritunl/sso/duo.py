from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings
from pritunl import logger

import base64
import email
import hmac
import hashlib
import urllib
import httplib
import requests

def _sign(method, path, params):
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

def auth_duo(username, strong=False, ipaddr=None, type=None, info=None,
        factor='push'):
    params = {
        'username': username,
        'factor': factor,
        'device': 'auto',
    }

    if ipaddr:
        params['ipaddr'] = ipaddr

    if factor == 'push':
        if type:
            params['type'] = type

        if info:
            params['pushinfo'] = urllib.urlencode(info)

    headers = _sign('POST', '/auth/v2/auth', params)
    url = 'https://%s/auth/v2/auth' % settings.app.sso_host

    try:
        response = requests.post(url,
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
            if SAML_DUO_AUTH in settings.app.sso and \
                    settings.app.sso_saml_duo_skip_unavailable:
                logger.warning('Skipping duo auth with bypass',
                    'sso',
                    username=username,
                )
                allow = True
            else:
                allow = False
                logger.error('Cannot use Duo bypass with profile login',
                    'sso',
                    data=resp_data,
                )
        else:
            allow = True
    elif data.get('code') == 40002:
        if factor == 'push':
            return auth_duo(username, strong, ipaddr, type, info, 'phone')

        if SAML_DUO_AUTH in settings.app.sso and \
                settings.app.sso_saml_duo_skip_unavailable:
            logger.warning('Skipping duo auth for unavailable user', 'sso',
                username=username,
            )
            allow = True
        else:
            raise InvalidUser('Invalid username')
    else:
        allow = False
        logger.error('Duo authentication failure', 'sso',
            data=data,
        )

    return allow, None
