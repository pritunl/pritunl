from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings
from pritunl import logger

import base64
import email
import hmac
import hashlib
import urllib.request, urllib.parse, urllib.error
import requests

def _sign(method, path, params):
    now = email.Utils.formatdate()
    canon = [now, method.upper(), settings.app.sso_duo_host.lower(), path]
    args = []
    for key in sorted(params.keys()):
        val = params[key]
        if isinstance(val, str):
            val = val.encode("utf-8")
        args.append('%s=%s' % (
            urllib.parse.quote(key, '~'),
            urllib.parse.quote(val, '~'),
        ))
    canon.append('&'.join(args))
    canon = '\n'.join(canon)

    sig = hmac.new(
        settings.app.sso_duo_secret.encode(),
        canon.encode(),
        hashlib.sha1,
    )
    auth = '%s:%s' % (settings.app.sso_duo_token.encode(), sig.hexdigest())

    return {
        'Date': now,
        'Authorization': 'Basic %s' % base64.b64encode(auth),
    }

class Duo(object):
    def __init__(self, username, factor=None, remote_ip=None, auth_type=None,
            info=None, passcode=None):
        self.username = username
        self.factor = factor
        self.remote_ip = remote_ip
        self.auth_type = auth_type
        self.info = info
        self.passcode = passcode
        self._interrupt = False
        self._valid = False

    def authenticate(self):
        if self.factor == 'phone':
            factor = 'phone'
        elif self.factor == 'passcode':
            factor = 'passcode'
        else:
            factor = 'push'

        self._auth(factor)
        return self._valid

    def _auth(self, factor):
        params = {
            'username': self.username,
            'factor': factor,
        }

        if self.remote_ip:
            params['ipaddr'] = self.remote_ip

        if factor in ('push', 'phone'):
            params['device'] = 'auto'

        if factor == 'push':
            if self.auth_type:
                params['type'] = self.auth_type

            if self.info:
                params['pushinfo'] = urllib.parse.urlencode(self.info)

        if factor == 'passcode':
            params['passcode'] = self.passcode

        headers = _sign('POST', '/auth/v2/auth', params)
        url = 'https://%s/auth/v2/auth' % settings.app.sso_duo_host

        try:
            response = requests.post(url,
                headers=headers,
                params=params,
                timeout=30,
            )
        except:
            if factor == 'push' and self.factor == 'push_phone':
                self._auth('phone')
                return
            else:
                raise

        data = response.json()
        resp_data = data.get('response')
        if resp_data and resp_data.get('result') == 'allow':
            if resp_data.get('status') == 'bypass':
                if settings.app.sso == DUO_AUTH:
                    logger.error('Cannot use Duo bypass with Duo sso',
                        'sso',
                        data=resp_data,
                    )
                    return
                else:
                    logger.info('Skipping Duo auth with bypass',
                        'sso',
                        username=self.username,
                    )
            self._valid = True
        elif data.get('code') == 40002:
            if factor == 'push' and self.factor == 'push_phone':
                self._auth('phone')
            else:
                logger.error('Invalid Duo username',
                    'sso',
                    username=self.username,
                    data=data,
                )
                raise InvalidUser('Invalid username')
        else:
            logger.error('Duo authentication failure', 'sso',
                data=data,
            )
