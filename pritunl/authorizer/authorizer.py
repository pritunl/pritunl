from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import logger
from pritunl import settings
from pritunl import sso
from pritunl import plugins
from pritunl import utils
from pritunl import mongo
from pritunl import tunldb
from pritunl import ipaddress

import threading
import uuid
import hashlib
import base64
import datetime

_states = tunldb.TunlDB()

class Authorizer(object):
    def __init__(self, svr, usr, remote_ip, plaform, device_id, device_name,
            mac_addr, password, auth_token, reauth, callback):
        self.server = svr
        self.user = usr
        self.remote_ip = remote_ip
        self.platform = plaform
        self.device_id = device_id
        self.device_name = device_name
        self.mac_addr = mac_addr
        self.password = password
        self.auth_token = auth_token
        self.reauth = reauth
        self.callback = callback
        self.state = None
        self.push_type = None
        self.challenge = None
        self.has_token = False
        self.whitelisted = False

        if self.password and self.password.startswith('CRV1:'):
            challenge = self.password.split(':')
            if len(challenge) == 5:
                self.state = challenge[2]
                self.password = challenge[4]

    @property
    def sso_passcode_cache_collection(cls):
        return mongo.get_collection('sso_passcode_cache')

    @property
    def sso_push_cache_collection(cls):
        return mongo.get_collection('sso_push_cache')

    @property
    def sso_client_cache_collection(cls):
        return mongo.get_collection('sso_client_cache')

    @property
    def limiter_collection(cls):
        return mongo.get_collection('auth_limiter')

    @property
    def otp_cache_collection(cls):
        return mongo.get_collection('otp_cache')

    def authenticate(self):
        try:
            self._check_call(self._check_primary)
            self._check_call(self._check_token)
            self._check_call(self._check_whitelist)
            self._check_call(self._check_password)
            self._check_call(self._check_sso)
            self._check_call(self._auth_plugins)
            self._check_call(self._check_push)
            self._callback(True)
        except:
            pass

    def has_challenge(self):
        return not self.state

    def set_challenge(self, password, msg, show):
        password = password or ''
        state = uuid.uuid4().hex
        key = str(self.user.id)
        _states.set(key, state + ':' + password[:256])
        _states.expire(key, 120)
        self.challenge = 'CRV1:R%s:%s:bmls:%s' % (
            (',E' if show else ''), state, msg)

    def get_challenge(self):
        if not self.state:
            return

        key = str(self.user.id)

        data = _states.get(key)
        if not data:
            return

        state, password = data.split(':', 1)
        if self.state == state:
            if not password and self.user.has_pin():
                self.state = None
            else:
                return password

    def _check_call(self, func):
        try:
            func()
        except AuthError, err:
            self._callback(False, str(err))
            raise
        except AuthForked:
            raise
        except:
            logger.exception('Exception in user authorize', 'authorize')
            self._callback(False, 'Unknown error occurred')
            raise

    def _callback(self, allow, reason=None):
        if allow:
            try:
                self._check_call(self._update_token)
            except:
                return

        self.callback(allow, reason)

    def _check_token(self):
        if settings.app.sso_client_cache and self.auth_token:
            doc = self.sso_client_cache_collection.find_one({
                'user_id': self.user.id,
                'server_id': self.server.id,
                'device_id': self.device_id,
                'device_name': self.device_name,
                'auth_token': self.auth_token,
            })
            if doc:
                self.has_token = True

    def _check_whitelist(self):
        if settings.app.sso_whitelist:
            remote_ip = ipaddress.IPAddress(self.remote_ip)

            for network_str in settings.app.sso_whitelist:
                try:
                    network = ipaddress.IPNetwork(network_str)
                except (ipaddress.AddressValueError, ValueError):
                    logger.warning('Invalid whitelist network', 'authorize',
                        network=network_str,
                    )
                    continue

                if remote_ip in network:
                    self.whitelisted = True
                    break

    def _update_token(self):
        if settings.app.sso_client_cache and self.auth_token and \
                not self.has_token:
            self.sso_client_cache_collection.update({
                'user_id': self.user.id,
                'server_id': self.server.id,
                'device_id': self.device_id,
                'device_name': self.device_name,
            }, {
                'user_id': self.user.id,
                'server_id': self.server.id,
                'device_id': self.device_id,
                'device_name': self.device_name,
                'auth_token': self.auth_token,
                'timestamp': utils.now(),
            }, upsert=True)

    def _check_primary(self):
        if self.user.disabled:
            self.user.audit_event('user_connection',
                'User connection to "%s" denied. User is disabled' % (
                    self.server.name),
                remote_addr=self.remote_ip,
            )
            raise AuthError('User is disabled')

        if self.user.link_server_id:
            return

        if not self.server.check_groups(self.user.groups):
            self.user.audit_event(
                'user_connection',
                ('User connection to "%s" denied. User not in ' +
                 'servers groups') % (self.server.name),
                remote_addr=self.remote_ip,
            )
            raise AuthError('User not in servers groups')

        if self.server.allowed_devices:
            if self.server.allowed_devices == 'mobile':
                platforms = MOBILE_PLATFORMS
            elif self.server.allowed_devices == 'desktop':
                platforms = DESKTOP_PLATFORMS
            else:
                logger.error('Unknown allowed devices option',
                    'server',
                    server_id=self.server.id,
                    allowed_devices=self.server.allowed_devices,
                )
                platforms = {}

            if self.platform not in platforms:
                self.user.audit_event(
                    'user_connection',
                    ('User connection to "%s" denied. User platform ' +
                     'not allowed') % (self.server.name),
                    remote_addr=self.remote_ip,
                )
                raise AuthError(
                    'User platform %s not allowed' % self.platform)

    def _check_password(self):
        if self.user.bypass_secondary or self.user.link_server_id or \
                settings.vpn.stress_test or self.has_token or self.whitelisted:
            return

        doc = self.limiter_collection.find_and_modify({
            '_id': self.user.id,
        }, {
            '$inc': {'count': 1},
            '$setOnInsert': {'timestamp': utils.now()},
        }, new=True, upsert=True)

        if utils.now() > doc['timestamp'] + datetime.timedelta(
                seconds=settings.app.auth_limiter_ttl):
            doc = {
                'count': 1,
                'timestamp': utils.now(),
            }
            self.limiter_collection.update({
                '_id': self.user.id,
            }, doc, upsert=True)

        if doc['count'] > settings.app.auth_limiter_count_max:
            self.user.audit_event(
                'user_connection',
                ('User connection to "%s" denied. Too many ' +
                 'authentication attempts') % (self.server.name),
                remote_addr=self.remote_ip,
            )
            raise AuthError('Too many authentication attempts')

        sso_mode = settings.app.sso or ''
        duo_mode = settings.app.sso_duo_mode
        auth_type = self.user.auth_type or ''
        if DUO_AUTH in sso_mode and DUO_AUTH in auth_type and \
                duo_mode == 'passcode':
            if not self.password and self.has_challenge() and \
                self.user.has_pin():
                self.set_challenge(None, 'Enter Pin', False)
                raise AuthError('Challenge pin')

            challenge = self.get_challenge()
            if challenge:
                self.password = challenge + self.password

            passcode_len = settings.app.sso_duo_passcode_length
            orig_password = self.password
            passcode = self.password[-passcode_len:]
            self.password = self.password[:-passcode_len]

            allow = False
            if settings.app.sso_cache:
                doc = self.sso_passcode_cache_collection.find_one({
                    'user_id': self.user.id,
                    'server_id': self.server.id,
                    'remote_ip': self.remote_ip,
                    'mac_addr': self.mac_addr,
                    'platform': self.platform,
                    'device_id': self.device_id,
                    'device_name': self.device_name,
                    'passcode': passcode,
                })
                if doc:
                    self.sso_passcode_cache_collection.update({
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': passcode,
                    }, {
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': passcode,
                        'timestamp': utils.now(),
                    })
                    allow = True

            if not allow:
                duo_auth = sso.Duo(
                    username=self.user.name,
                    factor=duo_mode,
                    remote_ip=self.remote_ip,
                    auth_type='Connection',
                    passcode=passcode,
                )
                allow = duo_auth.authenticate()

                if not allow:
                    if self.has_challenge():
                        if self.user.has_password(self.server):
                            self.set_challenge(
                                orig_password, 'Enter Duo Passcode', True)
                        else:
                            self.set_challenge(
                                None, 'Enter Duo Passcode', True)
                        raise AuthError('Challenge Duo code')

                    self.user.audit_event('user_connection',
                        ('User connection to "%s" denied. ' +
                         'User failed Duo passcode authentication') % (
                            self.server.name),
                        remote_addr=self.remote_ip,
                    )
                    raise AuthError('Invalid OTP code')

                if settings.app.sso_cache:
                    self.sso_passcode_cache_collection.update({
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'mac_addr': self.mac_addr,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                    }, {
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': passcode,
                        'timestamp': utils.now(),
                    }, upsert=True)

        elif YUBICO_AUTH in sso_mode and YUBICO_AUTH in auth_type:
            if not self.password and self.has_challenge() and \
                    self.user.has_pin():
                self.set_challenge(None, 'Enter Pin', False)
                raise AuthError('Challenge pin')

            challenge = self.get_challenge()
            if challenge:
                self.password = challenge + self.password

            orig_password = self.password
            yubikey = self.password[-44:]
            self.password = self.password[:-44]

            yubikey_hash = hashlib.sha512()
            yubikey_hash.update(yubikey)
            yubikey_hash = base64.b64encode(yubikey_hash.digest())

            allow = False
            if settings.app.sso_cache:
                doc = self.sso_passcode_cache_collection.find_one({
                    'user_id': self.user.id,
                    'server_id': self.server.id,
                    'remote_ip': self.remote_ip,
                    'mac_addr': self.mac_addr,
                    'platform': self.platform,
                    'device_id': self.device_id,
                    'device_name': self.device_name,
                    'passcode': yubikey_hash,
                })
                if doc:
                    self.sso_passcode_cache_collection.update({
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': yubikey_hash,
                    }, {
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': yubikey_hash,
                        'timestamp': utils.now(),
                    })
                    allow = True

            if not allow:
                valid, yubico_id = sso.auth_yubico(yubikey)
                if yubico_id != self.user.yubico_id:
                    valid = False

                if not valid:
                    if self.has_challenge():
                        if self.user.has_password(self.server):
                            self.set_challenge(
                                orig_password, 'YubiKey', True)
                        else:
                            self.set_challenge(
                                None, 'YubiKey', True)
                        raise AuthError('Challenge YubiKey')

                    self.user.audit_event('user_connection',
                        ('User connection to "%s" denied. ' +
                         'User failed Yubico authentication') % (
                            self.server.name),
                        remote_addr=self.remote_ip,
                        )
                    raise AuthError('Invalid YubiKey')

                if settings.app.sso_cache:
                    self.sso_passcode_cache_collection.update({
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'mac_addr': self.mac_addr,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                    }, {
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': yubikey_hash,
                        'timestamp': utils.now(),
                    }, upsert=True)

        elif self.server.otp_auth and self.user.type == CERT_CLIENT:
            if not self.password and self.has_challenge() and \
                    self.user.has_pin():
                self.set_challenge(None, 'Enter Pin', False)
                raise AuthError('Challenge pin')

            challenge = self.get_challenge()
            if challenge:
                self.password = challenge + self.password

            orig_password = self.password
            otp_code = self.password[-6:]
            self.password = self.password[:-6]

            allow = False
            if settings.vpn.otp_cache:
                doc = self.otp_cache_collection.find_one({
                    'user_id': self.user.id,
                    'server_id': self.server.id,
                    'remote_ip': self.remote_ip,
                    'mac_addr': self.mac_addr,
                    'platform': self.platform,
                    'device_id': self.device_id,
                    'device_name': self.device_name,
                    'passcode': otp_code,
                })
                if doc:
                    self.otp_cache_collection.update({
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': otp_code,
                    }, {
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': otp_code,
                        'timestamp': utils.now(),
                    })
                    allow = True

            if not allow:
                if not self.user.verify_otp_code(otp_code):
                    if self.has_challenge():
                        if self.user.has_password(self.server):
                            self.set_challenge(
                                orig_password, 'Enter OTP Code', True)
                        else:
                            self.set_challenge(
                                None, 'Enter OTP Code', True)
                        raise AuthError('Challenge OTP code')

                    self.user.audit_event('user_connection',
                        ('User connection to "%s" denied. ' +
                         'User failed two-step authentication') % (
                            self.server.name),
                        remote_addr=self.remote_ip,
                    )
                    raise AuthError('Invalid OTP code')

                if settings.vpn.otp_cache:
                    self.otp_cache_collection.update({
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'mac_addr': self.mac_addr,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                    }, {
                        'user_id': self.user.id,
                        'server_id': self.server.id,
                        'remote_ip': self.remote_ip,
                        'mac_addr': self.mac_addr,
                        'platform': self.platform,
                        'device_id': self.device_id,
                        'device_name': self.device_name,
                        'passcode': otp_code,
                        'timestamp': utils.now(),
                    }, upsert=True)

        if self.user.has_pin():
            if not self.user.check_pin(self.password):
                if self.has_challenge():
                    self.set_challenge(None, 'Enter Pin', False)
                    raise AuthError('Challenge pin')

                self.user.audit_event('user_connection',
                    ('User connection to "%s" denied. ' +
                     'User failed pin authentication') % (
                        self.server.name),
                    remote_addr=self.remote_ip,
                )
                raise AuthError('Invalid pin')
        elif settings.user.pin_mode == PIN_REQUIRED:
            self.user.audit_event('user_connection',
                ('User connection to "%s" denied. ' +
                 'User does not have a pin set') % (
                    self.server.name),
                remote_addr=self.remote_ip,
            )
            raise AuthError('User does not have a pin set')

    def _check_sso(self):
        if self.user.bypass_secondary or settings.vpn.stress_test:
            return

        if not self.user.sso_auth_check(self.password, self.remote_ip):
            self.user.audit_event('user_connection',
                ('User connection to "%s" denied. ' +
                 'Single sign-on authentication failed') % (
                    self.server.name),
                remote_addr=self.remote_ip,
            )
            raise AuthError('Failed secondary authentication')

    def _check_push(self):
        if self.user.bypass_secondary or settings.vpn.stress_test or \
                self.has_token or self.whitelisted:
            return

        self.push_type = self.user.get_push_type()
        if not self.push_type:
            return

        if settings.app.sso_cache:
            doc = self.sso_push_cache_collection.find_one({
                'user_id': self.user.id,
                'server_id': self.server.id,
                'remote_ip': self.remote_ip,
                'mac_addr': self.mac_addr,
                'platform': self.platform,
                'device_id': self.device_id,
                'device_name': self.device_name,
            })
            if doc:
                self.sso_push_cache_collection.update({
                    'user_id': self.user.id,
                    'server_id': self.server.id,
                    'mac_addr': self.mac_addr,
                    'device_id': self.device_id,
                    'device_name': self.device_name,
                }, {
                    'user_id': self.user.id,
                    'server_id': self.server.id,
                    'remote_ip': self.remote_ip,
                    'mac_addr': self.mac_addr,
                    'platform': self.platform,
                    'device_id': self.device_id,
                    'device_name': self.device_name,
                    'timestamp': utils.now(),
                })
                return

        def thread_func():
            try:
                self._check_call(self._auth_push_thread)
                self._callback(True)
            except:
                pass

        thread = threading.Thread(target=thread_func)
        thread.daemon = True
        thread.start()

        raise AuthForked()

    def _auth_push_thread(self):
        info = {
            'Server': self.server.name,
        }

        platform_name = None
        if self.platform == 'linux':
            platform_name = 'Linux'
        elif self.platform == 'mac':
            platform_name = 'macOS'
        elif self.platform == 'ios':
            platform_name = 'iOS'
        elif self.platform == 'win':
            platform_name = 'Windows'
        elif self.platform == 'chrome':
            platform_name = 'Chrome OS'

        if self.device_name:
            info['Device'] = '%s (%s)' % (self.device_name, platform_name)

        if self.push_type == DUO_AUTH:
            duo_auth = sso.Duo(
                username=self.user.name,
                factor=settings.app.sso_duo_mode,
                remote_ip=self.remote_ip,
                auth_type='Connection',
                info=info,
            )
            allow = duo_auth.authenticate()
        elif self.push_type == SAML_OKTA_AUTH:
            allow = sso.auth_okta_push(
                self.user.name,
                ipaddr=self.remote_ip,
                type='Connection',
                info=info,
            )
        else:
            raise ValueError('Unkown push auth type')

        if not allow:
            self.user.audit_event('user_connection',
                ('User connection to "%s" denied. ' +
                 'Push authentication failed') % (
                    self.server.name),
                remote_addr=self.remote_ip,
            )
            raise AuthError('User failed push authentication')

        if settings.app.sso_cache:
            self.sso_push_cache_collection.update({
                'user_id': self.user.id,
                'server_id': self.server.id,
                'mac_addr': self.mac_addr,
                'device_id': self.device_id,
                'device_name': self.device_name,
            }, {
                'user_id': self.user.id,
                'server_id': self.server.id,
                'remote_ip': self.remote_ip,
                'mac_addr': self.mac_addr,
                'platform': self.platform,
                'device_id': self.device_id,
                'device_name': self.device_name,
                'timestamp': utils.now(),
            }, upsert=True)

    def _auth_plugins(self):
        if not self.user.link_server_id and self.user.type == CERT_CLIENT:
            returns = plugins.caller(
                'user_connect',
                host_id=settings.local.host_id,
                server_id=self.server.id,
                org_id=self.user.org.id,
                user_id=self.user.id,
                host_name=settings.local.host.name,
                server_name=self.server.name,
                org_name=self.user.org.name,
                user_name=self.user.name,
                remote_ip=self.remote_ip,
                platform=self.platform,
                device_name=self.device_name,
                password=self.password,
            )

            if not returns:
                return

            for return_val in returns:
                if not return_val[0]:
                    raise AuthError(return_val[1])
