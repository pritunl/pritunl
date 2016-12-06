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
import time
import threading

def _sign(method, path, params):
    now = email.Utils.formatdate()
    canon = [now, method.upper(), settings.app.sso_duo_host.lower(), path]
    args = []
    for key in sorted(params.keys()):
        val = params[key]
        if isinstance(val, unicode):
            val = val.encode("utf-8")
        args.append(
            '%s=%s' % (urllib.quote(key, '~'), urllib.quote(val, '~')))
    canon.append('&'.join(args))
    canon = '\n'.join(canon)

    sig = hmac.new(settings.app.sso_duo_secret.encode(), canon, hashlib.sha1)
    auth = '%s:%s' % (settings.app.sso_duo_token.encode(), sig.hexdigest())

    return {
        'Date': now,
        'Authorization': 'Basic %s' % base64.b64encode(auth),
    }

def auth_duo(username, strong=False, ipaddr=None, type=None, info=None,
        factor='push', thread=True):
    if factor == 'push' and thread:
        state = {
            'interrupt': False,
            'valid': None,
            'org_id': None,
            'exception': None,
        }
        state_lock = threading.Lock()
        state_event = threading.Event()

        def phone_thread():
            start = time.time()
            backup_delay = settings.app.sso_duo_backup_delay

            while True:
                if state['interrupt']:
                    return
                if time.time() - start >= backup_delay:
                    break
                time.sleep(0.1)

            try:
                valid, org_id = auth_duo(
                    username,
                    strong=strong,
                    ipaddr=ipaddr,
                    type=type,
                    info=info,
                    factor='phone',
                    thread=False,
                )
            except Exception as error:
                state_lock.acquire()
                try:
                    if state['interrupt']:
                        return
                    state['interrupt'] = True
                    state['exception'] = error
                    state_event.set()
                finally:
                    state_lock.release()
                return

            if not valid:
                return

            state_lock.acquire()
            try:
                if state['interrupt']:
                    return

                state['interrupt'] = True
                state['valid'] = valid
                state['org_id'] = org_id

                state_event.set()
            finally:
                state_lock.release()

        def push_thread():
            try:
                valid, org_id = auth_duo(
                    username,
                    strong=strong,
                    ipaddr=ipaddr,
                    type=type,
                    info=info,
                    factor='push',
                    thread=False,
                )
            except UserDuoPushUnavailable:
                state_lock.acquire()
                try:
                    if state['interrupt']:
                        return

                    state['interrupt'] = True
                finally:
                    state_lock.release()

                try:
                    valid, org_id = auth_duo(
                        username,
                        strong=strong,
                        ipaddr=ipaddr,
                        type=type,
                        info=info,
                        factor='phone',
                        thread=False,
                    )
                except Exception as error:
                    state['interrupt'] = True
                    state['exception'] = error
                    state_event.set()
                    return

                state['valid'] = valid
                state['org_id'] = org_id
                state_event.set()
                return
            except Exception as error:
                state_lock.acquire()
                try:
                    if state['interrupt']:
                        return
                    state['interrupt'] = True
                    state['exception'] = error
                    state_event.set()
                finally:
                    state_lock.release()
                return

            state_lock.acquire()
            try:
                if state['interrupt']:
                    return

                state['interrupt'] = True
                state['valid'] = valid
                state['org_id'] = org_id
                state_event.set()
            finally:
                state_lock.release()

        thread = threading.Thread(target=phone_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=push_thread)
        thread.daemon = True
        thread.start()

        state_event.wait()

        if state['exception']:
            raise state['exception']

        return state['valid'], state['org_id']

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
    url = 'https://%s/auth/v2/auth' % settings.app.sso_duo_host

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
            raise UserDuoPushUnavailable('Duo push is unavailable')

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
