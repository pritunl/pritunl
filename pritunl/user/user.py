from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import utils
from pritunl import queue
from pritunl import logger
from pritunl import messenger
from pritunl import ipaddress
from pritunl import sso
from pritunl import auth
from pritunl import plugins

import tarfile
import zipfile
import os
import subprocess
import hashlib
import base64
import struct
import hmac
import json
import uuid
import pymongo
import urllib.request, urllib.parse, urllib.error
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed

class User(mongo.MongoObject):
    fields = {
        'org_id',
        'name',
        'email',
        'groups',
        'pin',
        'otp_secret',
        'type',
        'auth_type',
        'yubico_id',
        'disabled',
        'sync_token',
        'sync_secret',
        'private_key',
        'certificate',
        'resource_id',
        'link_server_id',
        'bypass_secondary',
        'client_to_client',
        'mac_addresses',
        'dns_servers',
        'dns_suffix',
        'port_forwarding',
    }
    fields_default = {
        'name': '',
        'disabled': False,
        'type': CERT_CLIENT,
        'auth_type': LOCAL_AUTH,
        'bypass_secondary': False,
        'client_to_client': False,
    }

    def __init__(self, org, name=None, email=None, pin=None, type=None,
            groups=None, auth_type=None, yubico_id=None, disabled=None,
            resource_id=None, bypass_secondary=None, client_to_client=None,
            mac_addresses=None, dns_servers=None, dns_suffix=None,
            port_forwarding=None, **kwargs):
        mongo.MongoObject.__init__(self)

        if org:
            self.org = org
            self.org_id = org.id
        else:
            self.org = None

        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if pin is not None:
            self.pin = pin
        if type is not None:
            self.type = type
        if groups is not None:
            self.groups = groups
        if auth_type is not None:
            self.auth_type = auth_type
        if yubico_id is not None:
            self.yubico_id = yubico_id
        if disabled is not None:
            self.disabled = disabled
        if resource_id is not None:
            self.resource_id = resource_id
        if bypass_secondary is not None:
            self.bypass_secondary = bypass_secondary
        if client_to_client is not None:
            self.client_to_client = client_to_client
        if mac_addresses is not None:
            self.mac_addresses = mac_addresses
        if dns_servers is not None:
            self.dns_servers = dns_servers
        if dns_suffix is not None:
            self.dns_suffix = dns_suffix
        if port_forwarding is not None:
            self.port_forwarding = port_forwarding

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def audit_collection(cls):
        return mongo.get_collection('users_audit')

    @cached_static_property
    def net_link_collection(cls):
        return mongo.get_collection('users_net_link')

    @cached_static_property
    def otp_collection(cls):
        return mongo.get_collection('otp')

    @cached_static_property
    def otp_cache_collection(cls):
        return mongo.get_collection('otp_cache')

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
    def has_duo_passcode(self):
        return settings.app.sso and self.auth_type and \
           DUO_AUTH in self.auth_type and \
           DUO_AUTH in settings.app.sso and \
           settings.app.sso_duo_mode == 'passcode'

    @property
    def has_onelogin_passcode(self):
        return settings.app.sso and self.auth_type and \
           SAML_ONELOGIN_AUTH in self.auth_type and \
           SAML_ONELOGIN_AUTH == settings.app.sso and \
           'passcode' in utils.get_onelogin_mode()

    @property
    def has_okta_passcode(self):
        return settings.app.sso and self.auth_type and \
           SAML_OKTA_AUTH in self.auth_type and \
           SAML_OKTA_AUTH == settings.app.sso and \
           'passcode' in utils.get_okta_mode()

    @property
    def has_yubikey(self):
        return self.auth_type == YUBICO_AUTH or (
            settings.app.sso and self.auth_type and \
            YUBICO_AUTH in self.auth_type and \
            YUBICO_AUTH in settings.app.sso)

    @property
    def journal_data(self):
        try:
            data = self.org.journal_data
        except:
            data = {}

        data.update({
            'user_id': self.id,
            'user_name': self.name,
            'user_email': self.email,
            'user_type': self.type,
            'user_auth_type': self.auth_type,
        })

        return data

    def dict(self):
        return {
            'id': self.id,
            'organization': self.org.id,
            'organization_name': self.org.name,
            'name': self.name,
            'email': self.email,
            'groups': self.groups or [],
            'pin': bool(self.pin),
            'type': self.type,
            'auth_type': self.auth_type,
            'yubico_id': self.yubico_id,
            'otp_secret': self.otp_secret,
            'disabled': self.disabled,
            'bypass_secondary': self.bypass_secondary,
            'client_to_client': self.client_to_client,
            'mac_addresses': self.mac_addresses,
            'dns_servers': self.dns_servers,
            'dns_suffix': self.dns_suffix,
            'port_forwarding': self.port_forwarding,
        }

    def initialize(self):
        temp_path = utils.get_temp_path()
        index_path = os.path.join(temp_path, INDEX_NAME)
        index_attr_path = os.path.join(temp_path, INDEX_ATTR_NAME)
        serial_path = os.path.join(temp_path, SERIAL_NAME)
        ssl_conf_path = os.path.join(temp_path, OPENSSL_NAME)
        reqs_path = os.path.join(temp_path, '%s.csr' % self.id)
        key_path = os.path.join(temp_path, '%s.key' % self.id)
        cert_path = os.path.join(temp_path, '%s.crt' % self.id)
        ca_name = self.id if self.type == CERT_CA else 'ca'
        ca_cert_path = os.path.join(temp_path, '%s.crt' % ca_name)
        ca_key_path = os.path.join(temp_path, '%s.key' % ca_name)

        self.org.queue_com.wait_status()

        try:
            os.makedirs(temp_path)

            with open(index_path, 'a'):
                os.utime(index_path, None)

            with open(index_attr_path, 'a'):
                os.utime(index_attr_path, None)

            with open(serial_path, 'w') as serial_file:
                serial_hex = ('%x' % utils.fnv64a(str(self.id))).upper()

                if len(serial_hex) % 2:
                    serial_hex = '0' + serial_hex

                serial_file.write('%s\n' % serial_hex)

            with open(ssl_conf_path, 'w') as conf_file:
                conf_file.write(CERT_CONF % (
                    settings.user.cert_key_bits,
                    settings.user.cert_message_digest,
                    self.org.id,
                    self.id,
                    index_path,
                    serial_path,
                    temp_path,
                    ca_cert_path,
                    ca_key_path,
                    settings.user.cert_message_digest,
                ))

            self.org.queue_com.wait_status()

            if self.type != CERT_CA:
                self.org.write_file(
                    'ca_certificate', ca_cert_path, chmod=0o600)
                self.org.write_file(
                    'ca_private_key', ca_key_path, chmod=0o600)
                self.generate_otp_secret()

            try:
                args = [
                    'openssl', 'req', '-new', '-batch',
                    '-config', ssl_conf_path,
                    '-out', reqs_path,
                    '-keyout', key_path,
                    '-reqexts', '%s_req_ext' % self.type.replace(
                        '_pool', ''),
                ]
                self.org.queue_com.popen(args)
            except (OSError, ValueError):
                logger.exception(
                    'Failed to create user cert requests', 'user',
                    org_id=self.org.id,
                    user_id=self.id,
                )
                raise
            self.read_file('private_key', key_path)

            try:
                args = ['openssl', 'ca', '-batch']

                if self.type == CERT_CA:
                    args += ['-selfsign']

                args += [
                    '-config', ssl_conf_path,
                    '-in', reqs_path,
                    '-out', cert_path,
                    '-extensions', '%s_ext' % self.type.replace('_pool', ''),
                ]

                self.org.queue_com.popen(args)
            except (OSError, ValueError):
                logger.exception('Failed to create user cert', 'user',
                    org_id=self.org.id,
                    user_id=self.id,
                )
                raise
            self.read_file('certificate', cert_path)
        finally:
            try:
                utils.rmtree(temp_path)
            except subprocess.CalledProcessError:
                pass

        self.org.queue_com.wait_status()

        # If assign ip addr fails it will be corrected in ip sync task
        try:
            self.assign_ip_addr()
        except:
            logger.exception('Failed to assign users ip address', 'user',
                org_id=self.org.id,
                user_id=self.id,
            )

    def queue_initialize(self, block, priority=LOW):
        if self.type in (CERT_SERVER_POOL, CERT_CLIENT_POOL):
            queue.start('init_user_pooled', block=block,
                org_doc=self.org.export(), user_doc=self.export(),
                priority=priority)
        else:
            retry = True
            if self.type == CERT_CA:
                retry = False

            queue.start('init_user', block=block, org_doc=self.org.export(),
                user_doc=self.export(), priority=priority, retry=retry)

        if block:
            self.load()

    def remove(self):
        self.audit_collection.remove({
            'user_id': self.id,
            'org_id': self.org_id,
        })
        self.net_link_collection.remove({
            'user_id': self.id,
            'org_id': self.org_id,
        })
        self.unassign_ip_addr()
        mongo.MongoObject.remove(self)

    def clear_auth_cache(self):
        self.sso_passcode_cache_collection.delete_many({
            'user_id': self.id,
        })
        self.sso_push_cache_collection.delete_many({
            'user_id': self.id,
        })
        self.sso_client_cache_collection.delete_many({
            'user_id': self.id,
        })
        messenger.publish('instance', ['user_disconnect', self.id])

    def disconnect(self):
        messenger.publish('instance', ['user_disconnect', self.id])

    def sso_auth_check(self, password, remote_ip):
        sso_mode = settings.app.sso or ''
        auth_server = AUTH_SERVER
        if settings.app.dedicated:
            auth_server = settings.app.dedicated

        if GOOGLE_AUTH in self.auth_type and GOOGLE_AUTH in sso_mode:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                resp = requests.get(auth_server +
                    '/update/google?user=%s&license=%s' % (
                        urllib.parse.quote(self.email),
                        settings.app.license,
                    ))

                if resp.status_code != 200:
                    logger.error('Google auth check request error', 'user',
                        user_id=self.id,
                        user_name=self.name,
                        status_code=resp.status_code,
                        content=resp.content,
                    )
                    return False

                valid, google_groups = sso.verify_google(self.email)
                if not valid:
                    logger.error('Google auth check failed', 'user',
                        user_id=self.id,
                        user_name=self.name,
                    )
                    return False

                if settings.app.sso_google_mode == 'groups':
                    cur_groups = set(self.groups)
                    new_groups = set(google_groups)

                    if cur_groups != new_groups:
                        self.groups = list(new_groups)
                        self.commit('groups')

                return True
            except:
                logger.exception('Google auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False
        elif AZURE_AUTH in self.auth_type and AZURE_AUTH in sso_mode:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                resp = requests.get(auth_server +
                    ('/update/azure?user=%s&license=%s&' +
                    'directory_id=%s&app_id=%s&app_secret=%s') % (
                        urllib.parse.quote(self.name),
                        settings.app.license,
                        urllib.parse.quote(settings.app.sso_azure_directory_id),
                        urllib.parse.quote(settings.app.sso_azure_app_id),
                        urllib.parse.quote(settings.app.sso_azure_app_secret),
                ))

                if resp.status_code != 200:
                    logger.error('Azure auth check request error', 'user',
                        user_id=self.id,
                        user_name=self.name,
                        status_code=resp.status_code,
                        content=resp.content,
                    )
                    return False

                valid, azure_groups = sso.verify_azure(self.name)
                if not valid:
                    logger.error('Azure auth check failed', 'user',
                        user_id=self.id,
                        user_name=self.name,
                    )
                    return False

                if settings.app.sso_azure_mode == 'groups':
                    cur_groups = set(self.groups)
                    new_groups = set(azure_groups)

                    if cur_groups != new_groups:
                        self.groups = list(new_groups)
                        self.commit('groups')

                return True
            except:
                logger.exception('Azure auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False
        elif AUTHZERO_AUTH in self.auth_type and AUTHZERO_AUTH in sso_mode:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                resp = requests.get(auth_server +
                    ('/update/authzero?user=%s&license=%s&' +
                     'app_domain=%s&app_id=%s&app_secret=%s') % (
                        urllib.parse.quote(self.name),
                        settings.app.license,
                        urllib.parse.quote(settings.app.sso_authzero_domain),
                        urllib.parse.quote(settings.app.sso_authzero_app_id),
                        urllib.parse.quote(settings.app.sso_authzero_app_secret),
                ))

                if resp.status_code != 200:
                    logger.error('Auth0 auth check request error', 'user',
                        user_id=self.id,
                        user_name=self.name,
                        status_code=resp.status_code,
                        content=resp.content,
                    )
                    return False

                valid, authzero_groups = sso.verify_authzero(self.name)
                if not valid:
                    logger.error('Auth0 auth check failed', 'user',
                        user_id=self.id,
                        user_name=self.name,
                    )
                    return False

                if settings.app.sso_authzero_mode == 'groups':
                    cur_groups = set(self.groups)
                    new_groups = set(authzero_groups)

                    if cur_groups != new_groups:
                        self.groups = list(new_groups)
                        self.commit('groups')

                return True
            except:
                logger.exception('Auth0 auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False
        elif SLACK_AUTH in self.auth_type and SLACK_AUTH in sso_mode:
            if settings.user.skip_remote_sso_check:
                return True

            if not isinstance(settings.app.sso_match, list):
                raise TypeError('Invalid sso match')

            try:
                resp = requests.get(auth_server +
                    '/update/slack?user=%s&team=%s&license=%s' % (
                        urllib.parse.quote(self.name),
                        urllib.parse.quote(settings.app.sso_match[0]),
                        settings.app.license,
                    ))

                if resp.status_code != 200:
                    logger.error('Slack auth check request error', 'user',
                        user_id=self.id,
                        user_name=self.name,
                        status_code=resp.status_code,
                        content=resp.content,
                    )
                    return False

                return True
            except:
                logger.exception('Slack auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False
        elif SAML_ONELOGIN_AUTH in self.auth_type and \
                SAML_ONELOGIN_AUTH in sso_mode:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                return sso.auth_onelogin(self.name)
            except:
                logger.exception('OneLogin auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False
        elif SAML_OKTA_AUTH in self.auth_type and \
                SAML_OKTA_AUTH in sso_mode:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                return sso.auth_okta(self.name)
            except:
                logger.exception('Okta auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False
        elif RADIUS_AUTH in self.auth_type and RADIUS_AUTH in sso_mode:
            try:
                return sso.verify_radius(self.name, password)[0]
            except:
                logger.exception('Radius auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False
        elif PLUGIN_AUTH in self.auth_type:
            try:
                return sso.plugin_login_authenticate(
                    user_name=self.name,
                    password=password,
                    remote_ip=remote_ip,
                )[1]
            except:
                logger.exception('Plugin auth check error', 'user',
                    user_id=self.id,
                    user_name=self.name,
                )
            return False

        return True

    def get_cache_key(self, suffix=None):
        if not self.cache_prefix:
            raise AttributeError(
                'Cached config object requires cache_prefix')

        key = self.cache_prefix + '-' + self.org.id + '_' + self.id
        if suffix:
            key += '-%s' % suffix

        return key

    def assign_ip_addr(self):
        for svr in self.org.iter_servers(fields=(
                'id', 'wg', 'network', 'network_wg', 'network_start',
                'network_end', 'network_lock')):
            svr.assign_ip_addr(self.org.id, self.id)

    def unassign_ip_addr(self):
        for svr in self.org.iter_servers(fields=(
                'id', 'wg', 'network', 'network_wg', 'network_start',
                'network_end', 'network_lock')):
            svr.unassign_ip_addr(self.org.id, self.id)

    def generate_otp_secret(self):
        self.otp_secret = utils.generate_otp_secret()

    def verify_otp_code(self, code):
        otp_secret = self.otp_secret
        padding = 8 - len(otp_secret) % 8
        if padding != 8:
            otp_secret = otp_secret.ljust(len(otp_secret) + padding, '=')
        otp_secret = base64.b32decode(otp_secret.upper())
        valid_codes = []
        epoch = int(utils.time_now() / 30)
        for epoch_offset in range(-1, 2):
            value = struct.pack('>q', epoch + epoch_offset)
            hmac_hash = hmac.new(otp_secret, value, hashlib.sha1).digest()
            offset = hmac_hash[-1] & 0x0F
            truncated_hash = hmac_hash[offset:offset + 4]
            truncated_hash = struct.unpack('>L', truncated_hash)[0]
            truncated_hash &= 0x7FFFFFFF
            truncated_hash %= 1000000
            valid_codes.append('%06d' % truncated_hash)

        if code not in valid_codes:
            return False

        try:
            self.otp_collection.insert({
                '_id': {
                    'user_id': self.id,
                    'code': code,
                },
                'timestamp': utils.now(),
            })
        except pymongo.errors.DuplicateKeyError:
            return False

        return True

    def _get_password_mode(self, svr):
        password_mode = None

        if self.bypass_secondary:
            return

        if settings.user.force_password_mode:
            return settings.user.force_password_mode

        if self.has_duo_passcode:
            password_mode = 'duo_otp'
        elif self.has_onelogin_passcode:
            password_mode = 'onelogin_otp'
        elif self.has_okta_passcode:
            password_mode = 'okta_otp'
        elif self.has_yubikey:
            password_mode = 'yubikey'
        elif svr.otp_auth:
            password_mode = 'otp'

        if (RADIUS_AUTH in self.auth_type and
                RADIUS_AUTH in settings.app.sso) or \
                PLUGIN_AUTH in self.auth_type:
            if password_mode:
                password_mode += '_password'
            else:
                password_mode = 'password'
        elif self.pin or settings.user.pin_mode == PIN_REQUIRED:
            if password_mode:
                password_mode += '_pin'
            else:
                password_mode = 'pin'

        return password_mode

    def _get_token_mode(self):
        return bool(settings.app.sso_client_cache)

    def has_passcode(self, svr):
        return bool(self.has_yubikey or self.has_duo_passcode or
            self.has_onelogin_passcode or self.has_okta_passcode or
            svr.otp_auth)

    def has_password(self, svr):
        return bool(self._get_password_mode(svr))

    def has_pin(self):
        return self.pin and settings.user.pin_mode != PIN_DISABLED

    def get_push_type(self):
        onelogin_mode = utils.get_onelogin_mode()
        okta_mode = utils.get_okta_mode()

        if settings.app.sso and DUO_AUTH in self.auth_type and \
                DUO_AUTH in settings.app.sso:
            if settings.app.sso_duo_mode != 'passcode':
                return DUO_AUTH
            return
        elif settings.app.sso and \
                SAML_ONELOGIN_AUTH in self.auth_type and \
                SAML_ONELOGIN_AUTH in settings.app.sso and \
                'push' in onelogin_mode:
            return SAML_ONELOGIN_AUTH
        elif settings.app.sso and \
                SAML_OKTA_AUTH in self.auth_type and \
                SAML_OKTA_AUTH in settings.app.sso and \
                'push' in okta_mode:
            return SAML_OKTA_AUTH

    def _get_key_info_str(self, svr, conf_hash, include_sync_keys):
        svr.generate_auth_key_commit()

        data = {
            'version': CLIENT_CONF_VER,
            'user': self.name,
            'organization': self.org.name,
            'server': svr.name,
            'wg': svr.wg,
            'user_id': str(self.id),
            'organization_id': str(self.org.id),
            'server_id': str(svr.id),
            'server_public_key': svr.auth_public_key.splitlines(),
            'server_box_public_key': svr.auth_box_public_key,
            'sync_hosts': svr.get_sync_remotes(),
            'sync_hash': conf_hash,
            'password_mode': self._get_password_mode(svr),
            'push_auth': True if self.get_push_type() else False,
            'push_auth_ttl': settings.app.sso_client_cache_timeout,
            'disable_reconnect': not settings.user.reconnect,
            'token_ttl': settings.app.sso_client_cache_timeout,
        }

        if settings.user.password_encryption:
            data['token'] = self._get_token_mode()
        else:
            data['token'] = False

        if svr.pre_connect_msg:
            data['pre_connect_msg'] = svr.pre_connect_msg

        if include_sync_keys:
            data['sync_token'] = self.sync_token
            data['sync_secret'] = self.sync_secret

        return "#" + json.dumps(
            data, indent=1, separators=(",", ": ")
        ).replace("\n", "\n#")

    def _generate_conf(self, svr, include_user_cert=True):
        if not self.sync_token or not self.sync_secret:
            self.sync_token = utils.generate_secret()
            self.sync_secret = utils.generate_secret()
            self.commit(('sync_token', 'sync_secret'))

        file_name = '%s_%s_%s.ovpn' % (
            self.org.name, self.name, svr.name)
        if not svr.ca_certificate:
            svr.generate_ca_cert()
        key_remotes = svr.get_key_remotes()
        ca_certificate = svr.ca_certificate
        certificate = utils.get_cert_block(self.certificate)
        private_key = self.private_key.strip()

        conf_hash = hashlib.md5()
        conf_hash.update(self.name.encode())
        conf_hash.update(self.org.name.encode())
        conf_hash.update(svr.name.encode())
        conf_hash.update(svr.protocol.encode())
        for key_remote in sorted(key_remotes):
            conf_hash.update(key_remote.encode())
        conf_hash.update(CIPHERS[svr.cipher].encode())
        conf_hash.update(HASHES[svr.hash].encode())
        conf_hash.update(str(svr.lzo_compression).encode())
        conf_hash.update(str(svr.block_outside_dns).encode())
        conf_hash.update(str(svr.otp_auth).encode())
        conf_hash.update(JUMBO_FRAMES[svr.jumbo_frames].encode())
        conf_hash.update(svr.adapter_type.encode())
        conf_hash.update(str(svr.ping_interval).encode())
        conf_hash.update(str(settings.vpn.server_poll_timeout).encode())
        conf_hash.update(ca_certificate.encode())
        conf_hash.update(self._get_key_info_str(svr, None, False).encode())

        plugin_config = ''
        if settings.local.sub_plan and \
                'enterprise' in settings.local.sub_plan:
            returns = plugins.caller(
                'user_config',
                host_id=settings.local.host_id,
                host_name=settings.local.host.name,
                org_id=self.org_id,
                user_id=self.id,
                user_name=self.name,
                server_id=svr.id,
                server_name=svr.name,
                server_port=svr.port,
                server_protocol=svr.protocol,
                server_ipv6=svr.ipv6,
                server_ipv6_firewall=svr.ipv6_firewall,
                server_network=svr.network,
                server_network6=svr.network6,
                server_network_mode=svr.network_mode,
                server_network_start=svr.network_start,
                server_network_stop=svr.network_end,
                server_restrict_routes=svr.restrict_routes,
                server_bind_address=svr.bind_address,
                server_onc_hostname=None,
                server_dh_param_bits=svr.dh_param_bits,
                server_multi_device=svr.multi_device,
                server_dns_servers=svr.dns_servers,
                server_search_domain=svr.search_domain,
                server_otp_auth=svr.otp_auth,
                server_cipher=svr.cipher,
                server_hash=svr.hash,
                server_inter_client=svr.inter_client,
                server_ping_interval=svr.ping_interval,
                server_ping_timeout=svr.ping_timeout,
                server_link_ping_interval=svr.link_ping_interval,
                server_link_ping_timeout=svr.link_ping_timeout,
                server_allowed_devices=svr.allowed_devices,
                server_max_clients=svr.max_clients,
                server_replica_count=svr.replica_count,
                server_dns_mapping=svr.dns_mapping,
                server_debug=svr.debug,
            )

            if returns:
                for return_val in returns:
                    if not return_val:
                        continue

                    val = return_val.strip()
                    conf_hash.update(val.encode())
                    plugin_config += val + '\n'

        conf_hash = conf_hash.hexdigest()

        client_conf = OVPN_INLINE_CLIENT_CONF % (
            self._get_key_info_str(svr, conf_hash, include_user_cert),
            uuid.uuid4().hex,
            utils.random_name(),
            svr.adapter_type,
            svr.adapter_type,
            svr.get_key_remotes(),
            CIPHERS[svr.cipher],
            HASHES[svr.hash],
            svr.ping_interval,
            svr.ping_timeout,
            settings.vpn.server_poll_timeout,
        )

        if svr.lzo_compression != ADAPTIVE:
            client_conf += 'comp-lzo no\n'

        if svr.block_outside_dns:
            client_conf += 'ignore-unknown-option block-outside-dns\n'
            client_conf += 'block-outside-dns\n'

        if self.has_password(svr):
            client_conf += 'auth-user-pass\n'

        if svr.tls_auth:
            client_conf += 'key-direction 1\n'

        client_conf += JUMBO_FRAMES[svr.jumbo_frames]
        client_conf += plugin_config
        client_conf += '<ca>\n%s\n</ca>\n' % ca_certificate
        if include_user_cert:
            if svr.tls_auth:
                client_conf += '<tls-auth>\n%s\n</tls-auth>\n' % (
                    svr.tls_auth_key)

            client_conf += '<cert>\n%s\n</cert>\n' % certificate
            client_conf += '<key>\n%s\n</key>\n' % private_key

        return file_name, client_conf, conf_hash

    def _generate_onc(self, svr, user_cert_id):
        if not svr.primary_organization or \
                not svr.primary_user:
            svr.create_primary_user()

        conf_hash = hashlib.md5()
        conf_hash.update(str(svr.id).encode())
        conf_hash.update(str(self.org_id).encode())
        conf_hash.update(str(self.id).encode())
        conf_hash = '{%s}' % conf_hash.hexdigest()

        hosts = svr.get_hosts()
        if not hosts:
            return None, None

        ca_certs = svr.ca_certificate_x509

        tls_auth = ''
        if svr.tls_auth:
            for line in svr.tls_auth_key.split('\n'):
                if line.startswith('#'):
                    continue
                tls_auth += line + '\\n'
            tls_auth = '\n          "TLSAuthContents": "%s",' % tls_auth
            tls_auth = '\n          "KeyDirection": "1",' + tls_auth

        onc_certs = {}
        cert_ids = []
        for cert in ca_certs:
            cert_id = '{%s}' % hashlib.md5(cert.encode()).hexdigest()
            onc_certs[cert_id] = cert
            cert_ids.append(cert_id)

        server_ref = ''
        for cert_id in cert_ids:
            server_ref += '            "%s",\n' % cert_id
        server_ref = server_ref[:-2]

        other = ''
        if not svr.is_route_all():
            other = '\n          "IgnoreDefaultRoute": true,'

        password_mode = self._get_password_mode(svr)
        if not password_mode:
            other += OVPN_ONC_AUTH_NONE % self.id
        else:
            has_otp = 'otp' in password_mode or 'yubikey' in password_mode
            has_pass = 'password' in password_mode or 'pin' in password_mode
            if has_otp and has_pass:
                other += OVPN_ONC_AUTH_PASS_OTP % self.id
            elif has_otp:
                other += OVPN_ONC_AUTH_OTP % self.id
            else:
                other += OVPN_ONC_AUTH_PASS % self.id

        primary_host = None
        primary_port = None
        extra_hosts = ''
        for host, port in hosts:
            if primary_host is None:
                primary_host = host
                primary_port = port
            else:
                extra_hosts += '            "%s:%s",\n' % (host, port)
        extra_hosts = extra_hosts[:-2]
        if extra_hosts:
            extra_hosts = '\n          "ExtraHosts": [\n%s\n        ],' % \
                extra_hosts

        onc_net = OVPN_ONC_NET_CONF % (
            conf_hash,
            '%s - %s (%s)' % (self.name, self.org.name, svr.name),
            primary_host,
            HASHES[svr.hash],
            ONC_CIPHERS[svr.cipher],
            user_cert_id,
            'adaptive' if svr.lzo_compression == ADAPTIVE else 'false',
            extra_hosts,
            primary_port,
            svr.protocol,
            server_ref,
            tls_auth,
            other,
        )

        return onc_net, onc_certs

    def iter_servers(self, fields=None):
        for svr in self.org.iter_servers(fields=fields):
            if not svr.check_groups(self.groups):
                continue
            yield svr

    def build_key_tar_archive(self):
        temp_path = utils.get_temp_path()
        key_archive_path = os.path.join(temp_path, '%s.tar' % self.id)

        try:
            os.makedirs(temp_path)
            tar_file = tarfile.open(key_archive_path, 'w')
            try:
                for svr in self.iter_servers():
                    server_conf_path = os.path.join(temp_path,
                        '%s_%s.ovpn' % (self.id, svr.id))
                    conf_name, client_conf, conf_hash = self._generate_conf(
                        svr)

                    with open(server_conf_path, 'w') as ovpn_conf:
                        os.chmod(server_conf_path, 0o600)
                        ovpn_conf.write(client_conf)
                    tar_file.add(server_conf_path, arcname=conf_name)
                    os.remove(server_conf_path)
            finally:
                tar_file.close()

            with open(key_archive_path, 'rb') as archive_file:
                key_archive = archive_file.read()
        finally:
            utils.rmtree(temp_path)

        return key_archive

    def build_key_zip_archive(self):
        temp_path = utils.get_temp_path()
        key_archive_path = os.path.join(temp_path, '%s.zip' % self.id)

        try:
            os.makedirs(temp_path)
            zip_file = zipfile.ZipFile(key_archive_path, 'w')
            try:
                for svr in self.iter_servers():
                    if not svr.check_groups(self.groups):
                        continue

                    server_conf_path = os.path.join(temp_path,
                        '%s_%s.ovpn' % (self.id, svr.id))
                    conf_name, client_conf, conf_hash = self._generate_conf(
                        svr)

                    with open(server_conf_path, 'w') as ovpn_conf:
                        os.chmod(server_conf_path, 0o600)
                        ovpn_conf.write(client_conf)
                    zip_file.write(server_conf_path, arcname=conf_name)
                    os.remove(server_conf_path)
            finally:
                zip_file.close()

            with open(key_archive_path, 'rb') as archive_file:
                key_archive = archive_file.read()
        finally:
            utils.rmtree(temp_path)

        return key_archive

    def build_onc(self):
        temp_path = utils.get_temp_path()

        try:
            os.makedirs(temp_path)

            user_cert_path = os.path.join(temp_path, '%s.crt' % self.id)
            user_key_path = os.path.join(temp_path, '%s.key' % self.id)
            user_p12_path = os.path.join(temp_path, '%s.p12' % self.id)

            with open(user_cert_path, 'w') as user_cert:
                user_cert.write(self.certificate)

            with open(user_key_path, 'w') as user_key:
                os.chmod(user_key_path, 0o600)
                user_key.write(self.private_key)

            utils.check_output_logged([
                'openssl',
                'pkcs12',
                '-export',
                '-nodes',
                '-password', 'pass:',
                '-inkey', user_key_path,
                '-in', user_cert_path,
                '-out', user_p12_path,
            ])

            with open(user_p12_path, 'rb') as user_key_p12:
                user_key_base64 = base64.b64encode(user_key_p12.read())
                user_cert_id = '{%s}' % hashlib.md5(
                    user_key_base64).hexdigest()

            os.remove(user_cert_path)
            os.remove(user_key_path)
            os.remove(user_p12_path)

            onc_nets = ''
            onc_certs_store = {}

            for svr in self.iter_servers():
                onc_net, onc_certs = self._generate_onc(
                    svr, user_cert_id)
                if not onc_net:
                    continue
                onc_certs_store.update(onc_certs)

                onc_nets += onc_net + ',\n'
            onc_nets = onc_nets[:-2]

            if onc_nets == '':
                return None

            onc_certs = ''
            for cert_id, cert in list(onc_certs_store.items()):
                onc_certs += OVPN_ONC_CA_CERT % (cert_id, cert) + ',\n'
            onc_certs += OVPN_ONC_CLIENT_CERT % (
                user_cert_id, user_key_base64)

            onc_conf = OVPN_ONC_CLIENT_CONF % (onc_nets, onc_certs)
        finally:
            utils.rmtree(temp_path)

        return onc_conf

    def get_server(self, server_id):
        svr = self.org.get_by_id(server_id)
        if not svr:
            raise NotFound('Server does not exists')

        if not svr.check_groups(self.groups):
            raise UserNotInServerGroups('User not in server groups')

        return svr

    def build_key_conf(self, server_id, include_user_cert=True):
        svr = self.get_server(server_id)

        conf_name, client_conf, conf_hash = self._generate_conf(svr,
            include_user_cert)

        return {
            'name': conf_name,
            'conf': client_conf,
            'hash': conf_hash,
        }

    def sync_conf(self, server_id, conf_hash):
        try:
            key = self.build_key_conf(server_id, False)
        except (NotFound, UserNotInServerGroups):
            return

        if key['hash'] != conf_hash:
            return key

    def check_pin(self, test_pin):
        if not self.pin or not test_pin:
            return False

        hash_ver, pin_salt, pin_hash = self.pin.split('$')

        if hash_ver == '1':
            hash_func = auth.hash_pin_v1
        elif hash_ver == '2':
            hash_func = auth.hash_pin_v2
        else:
            raise ValueError('Unknown hash version')

        test_hash = base64.b64encode(hash_func(pin_salt, test_pin)).decode()
        return test_hash == pin_hash

    def set_pin(self, pin):
        if not pin:
            changed = bool(self.pin)
            self.pin = None
            return changed

        changed = not self.check_pin(pin)
        self.pin = auth.generate_hash_pin_v2(pin)
        return changed

    def verify_sig(self, digest, signature):
        public_key = serialization.load_pem_private_key(
            self.private_key.encode(),
            password=None,
            backend=default_backend(),
        ).public_key()

        public_key.verify(
            signature,
            digest,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            Prehashed(hashes.SHA512()),
        )

    def send_key_email(self, key_link_domain):
        user_key_link = self.org.create_user_key_link(self.id)

        key_link = key_link_domain + user_key_link['view_url']
        uri_link = key_link_domain.replace('https', 'pritunl', 1).replace(
            'http', 'pritunl', 1) + user_key_link['uri_url']

        text_email = KEY_LINK_EMAIL_TEXT.format(
            key_link=key_link,
            uri_link=uri_link,
        )

        html_email = KEY_LINK_EMAIL_HTML.format(
            key_link=key_link,
            uri_link=uri_link,
        )

        utils.send_email(
            self.email,
            'Pritunl VPN Key',
            text_email,
            html_email,
        )

    def add_network_link(self, network, force=False):
        from pritunl import server

        if not force:
            for svr in self.iter_servers(('status', 'groups')):
                if svr.status == ONLINE:
                    raise ServerOnlineError('Server online')

        network = str(ipaddress.ip_network(network))

        self.net_link_collection.update({
            'user_id': self.id,
            'org_id': self.org_id,
            'network': network,
        }, {
            'user_id': self.id,
            'org_id': self.org_id,
            'network': network,
        }, upsert=True)

        if force:
            for svr in self.iter_servers(server.operation_fields):
                if svr.status == ONLINE:
                    logger.info(
                        'Restarting running server to add network link',
                        'user',
                    )
                    svr.restart()

    def remove_network_link(self, network):
        self.net_link_collection.remove({
            'user_id': self.id,
            'org_id': self.org_id,
            'network': network,
        })

    def get_network_links(self):
        links = []

        for doc in self.net_link_collection.find({
                    'user_id': self.id,
                }):
            links.append(doc['network'])

        return links

    def audit_event(self, event_type, event_msg, remote_addr=None, **kwargs):
        if settings.app.auditing != ALL:
            return

        timestamp = utils.now()

        org_name = None
        if self.org:
            org_name = self.org.name

        self.audit_collection.insert({
            'user_id': self.id,
            'user_name': self.name,
            'org_id': self.org_id,
            'org_name': org_name,
            'timestamp': timestamp,
            'type': event_type,
            'remote_addr': remote_addr,
            'message': event_msg,
        })

        plugins.event(
            'audit_event',
            host_id=settings.local.host_id,
            host_name=settings.local.host.name,
            user_id=self.id,
            user_name=self.name,
            org_id=self.org_id,
            org_name=org_name,
            timestamp=timestamp,
            type=event_type,
            remote_addr=remote_addr,
            message=event_msg,
            **kwargs
        )

    def get_audit_events(self):
        if settings.app.demo_mode:
            return DEMO_AUDIT_EVENTS

        events = []
        spec = {
            'user_id': self.id,
            'org_id': self.org_id,
        }

        for doc in self.audit_collection.find(spec).sort(
                'timestamp', pymongo.DESCENDING).limit(
                settings.user.audit_limit):
            doc['timestamp'] = int(doc['timestamp'].strftime('%s'))
            events.append(doc)

        return events
