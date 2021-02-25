from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import logger
from pritunl import settings
from pritunl import sso
from pritunl import plugins
from pritunl import mongo
from pritunl import tunldb
from pritunl import ipaddress
from pritunl import limiter
from pritunl import utils
from pritunl import journal

import threading
import uuid
import hashlib
import base64
import pymongo

_states = tunldb.TunlDB()

class Authorizer(object):
    def __init__(self, svr, usr, remote_ip, platform, device_id, device_name,
            mac_addr, mac_addrs, password, auth_password, auth_token,
            auth_nonce, auth_timestamp, reauth, callback):
        self.server = svr
        self.user = usr
        self.remote_ip = remote_ip
        self.platform = platform
        self.device_id = device_id
        self.device_name = device_name
        self.mac_addr = mac_addr
        self.mac_addrs = mac_addrs
        self.password = password
        self.auth_password = auth_password
        self.auth_token = auth_token
        self.auth_nonce = auth_nonce
        self.auth_timestamp = auth_timestamp
        self.server_auth_token = None
        self.reauth = reauth
        self.callback = callback
        self.state = None
        self.push_type = None
        self.challenge = None
        self.has_token = False
        self.whitelisted = False

        if self.mac_addr:
            self.mac_addr = self.mac_addr.lower()

        if self.mac_addrs:
            self.mac_addrs = [x.lower() for x in self.mac_addrs]

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

    @property
    def nonces_collection(cls):
        return mongo.get_collection('auth_nonces')

    @property
    def journal_data(self):
        return {
            'remote_address': self.remote_ip,
            'platform': self.platform,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'mac_addr': self.mac_addr,
            'auth_nonce': self.auth_nonce,
            'auth_timestamp': self.auth_timestamp,
            'reauth': self.reauth,
        }

    def authenticate(self):
        try:
            self._check_call(self._check_auth_data)
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
        except AuthError as err:
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
            journal.entry(
                journal.USER_CONNECT_SUCCESS,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User connected',
            )
            try:
                self._check_call(self._update_token)
            except:
                return

        self.callback(allow, reason)

    def _check_token(self):
        if settings.app.sso_client_cache and self.server_auth_token:
            doc = self.sso_client_cache_collection.find_one({
                'user_id': self.user.id,
                'server_id': self.server.id,
                'device_id': self.device_id,
                'device_name': self.device_name,
                'auth_token': self.server_auth_token,
            })
            if doc:
                self.has_token = True

    def _check_whitelist(self):
        if settings.app.sso_whitelist:
            remote_ip = ipaddress.ip_address(self.remote_ip)

            for network_str in settings.app.sso_whitelist:
                try:
                    network = ipaddress.ip_network(network_str)
                except (ipaddress.AddressValueError, ValueError):
                    logger.warning('Invalid whitelist network', 'authorize',
                        network=network_str,
                    )
                    continue

                if remote_ip in network:
                    self.whitelisted = True
                    break

    def _update_token(self):
        if settings.app.sso_client_cache and self.server_auth_token and \
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
                'auth_token': self.server_auth_token,
                'timestamp': utils.now(),
            }, upsert=True)

    def _check_auth_data(self):
        if not self.auth_token and not self.auth_nonce and \
                not self.auth_timestamp:
            return

        if not self.auth_nonce:
            self.user.audit_event(
                'user_connection',
                'User connection to "%s" denied. Auth data missing nonce' % \
                    self.server.name,
                remote_addr=self.remote_ip,
            )

            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Auth data missing nonce',
            )

            raise AuthError('Auth data missing nonce')

        if not self.auth_timestamp:
            self.user.audit_event(
                'user_connection',
                ('User connection to "%s" denied. ' +
                    'Auth data missing timestamp') % \
                    self.server.name,
                remote_addr=self.remote_ip,
            )

            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Auth data missing timestamp',
            )

            raise AuthError('Auth data missing timestamp')

        if abs(int(self.auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            self.user.audit_event(
                'user_connection',
                'User connection to "%s" denied. Auth timestamp expired' % \
                    self.server.name,
                remote_addr=self.remote_ip,
            )

            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Auth timestamp expired',
            )

            raise AuthError('Auth timestamp expired')

        if self.auth_token:
            auth_token_hash = hashlib.sha512()
            auth_token_hash.update(self.auth_token.encode())
            auth_token = base64.b64encode(auth_token_hash.digest()).decode()
        else:
            auth_token = None

        try:
            self.nonces_collection.insert({
                'token': self.user.id,
                'nonce': self.auth_nonce,
                'timestamp': utils.now(),
            })
        except pymongo.errors.DuplicateKeyError:
            self.user.audit_event(
                'user_connection',
                'User connection to "%s" denied. Duplicate nonce' % \
                self.server.name,
                remote_addr=self.remote_ip,
            )

            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Duplicate nonce',
            )

            raise AuthError('Duplicate nonce')

        self.password = self.auth_password
        self.server_auth_token = auth_token

    def _check_primary(self):
        org_matched = False
        for org_id in self.server.organizations:
            if self.user.org_id == org_id:
                org_matched = True
                break

        if not org_matched:
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Unknown organization',
            )
            raise AuthError('Unknown organization')

        if self.user.disabled:
            self.user.audit_event('user_connection',
                'User connection to "%s" denied. User is disabled' % (
                    self.server.name),
                remote_addr=self.remote_ip,
            )
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User disabled',
            )
            raise AuthError('User is disabled')

        if not self.user.name:
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User name empty',
            )
            raise AuthError('User name empty')

        user_lower = self.user.name.lower()
        if user_lower in INVALID_NAMES:
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User name invalid',
            )
            raise AuthError('User name invalid')

        if self.user.type == CERT_CLIENT:
            if self.user.link_server_id:
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Link user client type',
                )
                raise AuthError('Link user client type')
        elif self.user.type == CERT_SERVER:
            if not self.user.link_server_id:
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Link user missing server id',
                )
                raise AuthError('Link user missing server id')

            link_matched = False
            for link in self.server.links:
                if link.get('server_id') == self.user.link_server_id:
                    link_matched = True
                    break

            if not link_matched:
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Unknown link user',
                )
                raise AuthError('Unknown link user')

            return
        else:
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Unknown user type',
            )
            raise AuthError('Unknown user type')

        if not self.server.check_groups(self.user.groups):
            self.user.audit_event(
                'user_connection',
                ('User connection to "%s" denied. User not in ' +
                 'servers groups') % (self.server.name),
                remote_addr=self.remote_ip,
            )
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User not in servers groups',
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
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='User platform not allowed',
                )
                raise AuthError(
                    'User platform %s not allowed' % self.platform)

        if self.user.mac_addresses:
            allowed_mac_addrs = [x.lower() for x in self.user.mac_addresses]

            if self.mac_addrs:
                for mac_addr in self.mac_addrs:
                    if mac_addr in allowed_mac_addrs:
                        self.mac_addr = mac_addr

            if not self.mac_addr or self.mac_addr not in allowed_mac_addrs:
                self.user.audit_event(
                    'user_connection',
                    ('User connection to "%s" denied. User mac address' +
                     'not allowed') % (self.server.name),
                    mac_address=self.mac_addr,
                    remote_addr=self.remote_ip,
                )
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='User mac address not allowed',
                )
                raise AuthError(
                    'User mac address %s not allowed' % self.mac_addr)

    def _check_password(self):
        if settings.vpn.stress_test or self.user.link_server_id:
            return

        if self.user.bypass_secondary:
            logger.info(
                'Bypass secondary enabled, skipping password', 'sso',
                user_name=self.user.name,
                org_name=self.user.org.name,
                server_name=self.server.name,
            )
            journal.entry(
                journal.USER_CONNECT_BYPASS,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Bypass secondary enabled, skipping password',
            )
            return

        if self.has_token:
            logger.info(
                'Client authentication cached, skipping password', 'sso',
                user_name=self.user.name,
                org_name=self.user.org.name,
                server_name=self.server.name,
            )
            journal.entry(
                journal.USER_CONNECT_CACHE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Client authentication cached, skipping password',
            )
            return

        if self.whitelisted:
            logger.info(
                'Client network whitelisted, skipping password', 'sso',
                user_name=self.user.name,
                org_name=self.user.org.name,
                server_name=self.server.name,
            )
            journal.entry(
                journal.USER_CONNECT_WHITELIST,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Client network whitelisted, skipping password',
            )
            return

        if not limiter.auth_check(self.user.id):
            self.user.audit_event(
                'user_connection',
                ('User connection to "%s" denied. Too many ' +
                 'authentication attempts') % (self.server.name),
                remote_addr=self.remote_ip,
            )
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Too many authentication attempts',
            )
            raise AuthError('Too many authentication attempts')

        sso_mode = settings.app.sso or ''
        duo_mode = settings.app.sso_duo_mode
        onelogin_mode = utils.get_onelogin_mode()
        okta_mode = utils.get_okta_mode()
        auth_type = self.user.auth_type or ''

        has_duo_passcode = DUO_AUTH in sso_mode and \
            DUO_AUTH in auth_type and duo_mode == 'passcode'
        has_onelogin_passcode = SAML_ONELOGIN_AUTH == sso_mode and \
            SAML_ONELOGIN_AUTH in auth_type and onelogin_mode == 'passcode'
        has_okta_passcode = SAML_OKTA_AUTH == sso_mode and \
            SAML_OKTA_AUTH in auth_type and okta_mode == 'passcode'

        if has_duo_passcode or has_onelogin_passcode or has_okta_passcode:
            if not self.password and self.has_challenge() and \
                    self.user.has_pin():
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Failed pin authentication',
                )
                self.user.audit_event('user_connection',
                    ('User connection to "%s" denied. ' +
                     'User failed pin authentication') % (
                        self.server.name),
                    remote_addr=self.remote_ip,
                )
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
            if settings.app.sso_cache and not self.server_auth_token:
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

                    logger.info(
                        'Authentication cached, skipping secondary passcode',
                        'sso',
                        user_name=self.user.name,
                        org_name=self.user.org.name,
                        server_name=self.server.name,
                    )

                    journal.entry(
                        journal.USER_CONNECT_CACHE,
                        self.journal_data,
                        self.user.journal_data,
                        self.server.journal_data,
                        event_long='Authentication cached, ' + \
                            'skipping secondary passcode',
                    )

            if not allow:
                if DUO_AUTH in sso_mode:
                    label = 'Duo'
                    duo_auth = sso.Duo(
                        username=self.user.name,
                        factor=duo_mode,
                        remote_ip=self.remote_ip,
                        auth_type='Connection',
                        passcode=passcode,
                    )
                    allow = duo_auth.authenticate()
                elif SAML_ONELOGIN_AUTH == sso_mode:
                    label = 'OneLogin'
                    allow = sso.auth_onelogin_secondary(
                        username=self.user.name,
                        passcode=passcode,
                        remote_ip=self.remote_ip,
                        onelogin_mode=onelogin_mode,
                    )
                elif SAML_OKTA_AUTH == sso_mode:
                    label = 'Okta'
                    allow = sso.auth_okta_secondary(
                        username=self.user.name,
                        passcode=passcode,
                        remote_ip=self.remote_ip,
                        okta_mode=okta_mode,
                    )
                else:
                    raise AuthError('Unknown secondary passcode challenge')

                if not allow:
                    self.user.audit_event('user_connection',
                        ('User connection to "%s" denied. ' +
                         'User failed %s passcode authentication') % (
                            self.server.name, label),
                        remote_addr=self.remote_ip,
                    )
                    journal.entry(
                        journal.USER_CONNECT_FAILURE,
                        self.journal_data,
                        self.user.journal_data,
                        self.server.journal_data,
                        event_long='Failed passcode authentication',
                    )

                    if self.has_challenge():
                        if self.user.has_password(self.server):
                            self.set_challenge(
                                orig_password,
                                'Enter %s Passcode' % label, True)
                        else:
                            self.set_challenge(
                                None, 'Enter %s Passcode' % label, True)
                        raise AuthError('Challenge secondary passcode')
                    raise AuthError('Invalid secondary passcode')

                if settings.app.sso_cache and not self.server_auth_token:
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

        elif auth_type == YUBICO_AUTH or \
                (YUBICO_AUTH in sso_mode and YUBICO_AUTH in auth_type):
            if not self.password and self.has_challenge() and \
                    self.user.has_pin():
                self.user.audit_event('user_connection',
                    ('User connection to "%s" denied. ' +
                     'User failed pin authentication') % (
                        self.server.name),
                    remote_addr=self.remote_ip,
                )
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Failed pin authentication',
                )
                self.set_challenge(None, 'Enter Pin', False)
                raise AuthError('Challenge pin')

            challenge = self.get_challenge()
            if challenge:
                self.password = challenge + self.password

            orig_password = self.password
            yubikey = self.password[-44:]
            self.password = self.password[:-44]

            yubikey_hash = hashlib.sha512()
            yubikey_hash.update(yubikey.encode())
            yubikey_hash = base64.b64encode(yubikey_hash.digest()).decode()

            allow = False
            if settings.app.sso_cache and not self.server_auth_token:
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

                    logger.info(
                        'Authentication cached, skipping Yubikey', 'sso',
                        user_name=self.user.name,
                        org_name=self.user.org.name,
                        server_name=self.server.name,
                    )

                    journal.entry(
                        journal.USER_CONNECT_CACHE,
                        self.journal_data,
                        self.user.journal_data,
                        self.server.journal_data,
                        event_long='Authentication cached, ' + \
                            'skipping Yubikey',
                    )

            if not allow:
                valid, yubico_id = sso.auth_yubico(yubikey)
                if yubico_id != self.user.yubico_id:
                    valid = False

                if not valid:
                    self.user.audit_event('user_connection',
                        ('User connection to "%s" denied. ' +
                         'User failed Yubico authentication') % (
                            self.server.name),
                        remote_addr=self.remote_ip,
                    )
                    journal.entry(
                        journal.USER_CONNECT_FAILURE,
                        self.journal_data,
                        self.user.journal_data,
                        self.server.journal_data,
                        event_long='Failed Yubico authentication',
                    )

                    if self.has_challenge():
                        if self.user.has_password(self.server):
                            self.set_challenge(
                                orig_password, 'YubiKey', True)
                        else:
                            self.set_challenge(
                                None, 'YubiKey', True)
                        raise AuthError('Challenge YubiKey')
                    raise AuthError('Invalid YubiKey')

                if settings.app.sso_cache and not self.server_auth_token:
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
                self.user.audit_event('user_connection',
                    ('User connection to "%s" denied. ' +
                     'User failed pin authentication') % (
                        self.server.name),
                    remote_addr=self.remote_ip,
                )
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Failed pin authentication',
                )
                self.set_challenge(None, 'Enter Pin', False)
                raise AuthError('Challenge pin')

            challenge = self.get_challenge()
            if challenge:
                self.password = challenge + self.password

            orig_password = self.password
            otp_code = self.password[-6:]
            self.password = self.password[:-6]

            allow = False
            if settings.app.sso_cache and not self.server_auth_token:
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

                    logger.info(
                        'Authentication cached, skipping OTP', 'sso',
                        user_name=self.user.name,
                        org_name=self.user.org.name,
                        server_name=self.server.name,
                    )

                    journal.entry(
                        journal.USER_CONNECT_CACHE,
                        self.journal_data,
                        self.user.journal_data,
                        self.server.journal_data,
                        event_long='Authentication cached, ' + \
                            'skipping OTP',
                    )

            if not allow:
                if not self.user.verify_otp_code(otp_code):
                    self.user.audit_event('user_connection',
                        ('User connection to "%s" denied. ' +
                         'User failed two-step authentication') % (
                            self.server.name),
                        remote_addr=self.remote_ip,
                    )
                    journal.entry(
                        journal.USER_CONNECT_FAILURE,
                        self.journal_data,
                        self.user.journal_data,
                        self.server.journal_data,
                        event_long='Failed two-step authentication',
                    )

                    if self.has_challenge():
                        if self.user.has_password(self.server):
                            self.set_challenge(
                                orig_password, 'Enter OTP Code', True)
                        else:
                            self.set_challenge(
                                None, 'Enter OTP Code', True)
                        raise AuthError('Challenge OTP code')
                    raise AuthError('Invalid OTP code')

                if settings.app.sso_cache and not self.server_auth_token:
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
                self.user.audit_event('user_connection',
                    ('User connection to "%s" denied. ' +
                     'User failed pin authentication') % (
                        self.server.name),
                    remote_addr=self.remote_ip,
                )
                journal.entry(
                    journal.USER_CONNECT_FAILURE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Failed pin authentication',
                )

                if self.has_challenge():
                    self.set_challenge(None, 'Enter Pin', False)
                    raise AuthError('Challenge pin')
                raise AuthError('Invalid pin')
        elif settings.user.pin_mode == PIN_REQUIRED:
            self.user.audit_event('user_connection',
                ('User connection to "%s" denied. ' +
                 'User does not have a pin set') % (
                    self.server.name),
                remote_addr=self.remote_ip,
            )
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User does not have a pin set',
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
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Failed secondary authentication',
            )
            raise AuthError('Failed secondary authentication')

        if not self.server.check_groups(self.user.groups):
            self.user.audit_event(
                'user_connection',
                ('User connection to "%s" denied. User not in ' +
                 'servers groups') % (self.server.name),
                remote_addr=self.remote_ip,
            )
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User not in servers groups',
            )
            raise AuthError('User not in servers groups')

    def _check_push(self):
        self.push_type = self.user.get_push_type()
        if not self.push_type:
            return

        if settings.vpn.stress_test:
            return

        if self.user.bypass_secondary:
            logger.info('Bypass secondary enabled, skipping push', 'sso',
                user_name=self.user.name,
                org_name=self.user.org.name,
                server_name=self.server.name,
            )
            return

        if self.has_token:
            logger.info('Client authentication cached, skipping push', 'sso',
                user_name=self.user.name,
                org_name=self.user.org.name,
                server_name=self.server.name,
            )
            journal.entry(
                journal.USER_CONNECT_CACHE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Client authentication cached, skipping push',
            )
            return

        if self.whitelisted:
            logger.info('Client network whitelisted, skipping push', 'sso',
                user_name=self.user.name,
                org_name=self.user.org.name,
                server_name=self.server.name,
            )
            journal.entry(
                journal.USER_CONNECT_WHITELIST,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='Client network whitelisted, skipping push',
            )
            return

        if settings.app.sso_cache and not self.server_auth_token:
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

                logger.info('Authentication cached, skipping push', 'sso',
                    user_name=self.user.name,
                    org_name=self.user.org.name,
                    server_name=self.server.name,
                )

                journal.entry(
                    journal.USER_CONNECT_CACHE,
                    self.journal_data,
                    self.user.journal_data,
                    self.server.journal_data,
                    event_long='Authentication cached, skipping push',
                )

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

        onelogin_mode = utils.get_onelogin_mode()
        okta_mode = utils.get_okta_mode()

        if self.push_type == DUO_AUTH:
            duo_auth = sso.Duo(
                username=self.user.name,
                factor=settings.app.sso_duo_mode,
                remote_ip=self.remote_ip,
                auth_type='Connection',
                info=info,
            )
            allow = duo_auth.authenticate()
        elif self.push_type == SAML_ONELOGIN_AUTH:
            allow = sso.auth_onelogin_secondary(
                username=self.user.name,
                passcode=None,
                remote_ip=self.remote_ip,
                onelogin_mode=onelogin_mode,
            )
        elif self.push_type == SAML_OKTA_AUTH:
            allow = sso.auth_okta_secondary(
                username=self.user.name,
                passcode=None,
                remote_ip=self.remote_ip,
                okta_mode=okta_mode,
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
            journal.entry(
                journal.USER_CONNECT_FAILURE,
                self.journal_data,
                self.user.journal_data,
                self.server.journal_data,
                event_long='User failed push authentication',
            )
            raise AuthError('User failed push authentication')

        if settings.app.sso_cache and not self.server_auth_token:
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
                mac_addr=self.mac_addr,
                platform=self.platform,
                device_id=self.device_id,
                device_name=self.device_name,
                password=self.password,
            )

            if not returns:
                return

            for return_val in returns:
                if not return_val[0]:
                    raise AuthError(return_val[1])
