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
import urllib
import requests

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
        'disabled',
        'sync_token',
        'sync_secret',
        'private_key',
        'certificate',
        'resource_id',
        'link_server_id',
        'bypass_secondary',
        'client_to_client',
        'dns_servers',
        'dns_suffix',
        'port_forwarding',
    }
    fields_default = {
        'name': 'undefined',
        'disabled': False,
        'type': CERT_CLIENT,
        'auth_type': LOCAL_AUTH,
        'bypass_secondary': False,
        'client_to_client': False,
    }

    def __init__(self, org, name=None, email=None, pin=None, type=None,
            groups=None, auth_type=None, disabled=None, resource_id=None,
            bypass_secondary=None, client_to_client=None, dns_servers=None,
            dns_suffix=None, port_forwarding=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        self.org = org
        self.org_id = org.id

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
        if disabled is not None:
            self.disabled = disabled
        if resource_id is not None:
            self.resource_id = resource_id
        if bypass_secondary is not None:
            self.bypass_secondary = bypass_secondary
        if client_to_client is not None:
            self.client_to_client = client_to_client
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
            'otp_secret': self.otp_secret,
            'disabled': self.disabled,
            'bypass_secondary': self.bypass_secondary,
            'client_to_client': self.client_to_client,
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
                self.org.write_file('ca_certificate', ca_cert_path, chmod=0600)
                self.org.write_file('ca_private_key', ca_key_path, chmod=0600)
                self.generate_otp_secret()

            try:
                args = [
                    'openssl', 'req', '-new', '-batch',
                    '-config', ssl_conf_path,
                    '-out', reqs_path,
                    '-keyout', key_path,
                    '-reqexts', '%s_req_ext' % self.type.replace('_pool', ''),
                ]
                self.org.queue_com.popen(args)
            except (OSError, ValueError):
                logger.exception('Failed to create user cert requests', 'user',
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

    def disconnect(self):
        messenger.publish('instance', ['user_disconnect', self.id])

    def sso_auth_check(self, password, remote_ip):
        if GOOGLE_AUTH in self.auth_type and GOOGLE_AUTH in settings.app.sso:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                resp = requests.get(AUTH_SERVER +
                    '/update/google?user=%s&license=%s' % (
                        urllib.quote(self.email),
                        settings.app.license,
                    ))

                if resp.status_code == 200:
                    return True
            except:
                logger.exception('Google auth check error', 'user',
                    user_id=self.id,
                )
            return False
        elif SLACK_AUTH in self.auth_type and SLACK_AUTH in settings.app.sso:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                resp = requests.get(AUTH_SERVER +
                    '/update/slack?user=%s&team=%s&license=%s' % (
                        urllib.quote(self.name),
                        urllib.quote(settings.app.sso_match[0]),
                        settings.app.license,
                    ))

                if resp.status_code == 200:
                    return True
            except:
                logger.exception('Slack auth check error', 'user',
                    user_id=self.id,
                )
            return False
        elif SAML_ONELOGIN_AUTH in self.auth_type and \
                SAML_ONELOGIN_AUTH in settings.app.sso:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                return sso.auth_onelogin(self.name)
            except:
                logger.exception('OneLogin auth check error', 'user',
                    user_id=self.id,
                )
            return False
        elif SAML_OKTA_AUTH in self.auth_type and \
                SAML_OKTA_AUTH in settings.app.sso:
            if settings.user.skip_remote_sso_check:
                return True

            try:
                return sso.auth_okta(self.name)
            except:
                logger.exception('Okta auth check error', 'user',
                    user_id=self.id,
                )
            return False
        elif RADIUS_AUTH in self.auth_type and RADIUS_AUTH in settings.app.sso:
            try:
                return sso.verify_radius(self.name, password)[0]
            except:
                logger.exception('Radius auth check error', 'user',
                    user_id=self.id,
                )
            return False
        elif PLUGIN_AUTH in self.auth_type:
            try:
                return sso.plugin_login_authenticate(
                    user_name=self.name,
                    password=password,
                    remote_ip=remote_ip,
                )[0]
            except:
                logger.exception('Plugin auth check error', 'user',
                    user_id=self.id,
                )
            return False

        return True

    def get_cache_key(self, suffix=None):
        if not self.cache_prefix:
            raise AttributeError('Cached config object requires cache_prefix')

        key = self.cache_prefix + '-' + self.org.id + '_' + self.id
        if suffix:
            key += '-%s' % suffix

        return key

    def assign_ip_addr(self):
        for svr in self.org.iter_servers(fields=(
                'id', 'network', 'network_start',
                'network_end', 'network_lock')):
            svr.assign_ip_addr(self.org.id, self.id)

    def unassign_ip_addr(self):
        for svr in self.org.iter_servers(fields=(
                'id', 'network', 'network_start',
                'network_end', 'network_lock')):
            svr.unassign_ip_addr(self.org.id, self.id)

    def generate_otp_secret(self):
        self.otp_secret = utils.generate_otp_secret()

    def verify_otp_code(self, code, remote_ip=None):
        if remote_ip and settings.vpn.cache_otp_codes:
            doc = self.otp_cache_collection.find_one({
                '_id': self.id,
            })

            if doc:
                _, hash_salt, cur_otp_hash = doc['otp_hash'].split('$')
                hash_salt = base64.b64decode(hash_salt)
            else:
                hash_salt = os.urandom(8)
                cur_otp_hash = None

            otp_hash = hashlib.sha512()
            otp_hash.update(code + remote_ip)
            otp_hash.update(hash_salt)
            otp_hash = base64.b64encode(otp_hash.digest())

            if otp_hash == cur_otp_hash:
                self.otp_cache_collection.update({
                    '_id': self.id,
                }, {'$set': {
                    'timestamp': utils.now(),
                }})
                return True

            otp_hash = '$'.join((
                '1',
                base64.b64encode(hash_salt),
                otp_hash,
            ))

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
            offset = ord(hmac_hash[-1]) & 0x0F
            truncated_hash = hmac_hash[offset:offset + 4]
            truncated_hash = struct.unpack('>L', truncated_hash)[0]
            truncated_hash &= 0x7FFFFFFF
            truncated_hash %= 1000000
            valid_codes.append('%06d' % truncated_hash)

        if code not in valid_codes:
            return False

        response = self.otp_collection.update({
            '_id': {
                'user_id': self.id,
                'code': code,
            },
        }, {'$set': {
            'timestamp': utils.now(),
        }}, upsert=True)

        if response['updatedExisting']:
            return False

        if remote_ip and settings.vpn.cache_otp_codes:
            self.otp_cache_collection.update({
                '_id': self.id,
            }, {'$set': {
                'otp_hash': otp_hash,
                'timestamp': utils.now(),
            }}, upsert=True)

        return True

    def _get_password_mode(self, svr):
        password_mode = None

        if self.bypass_secondary:
            return

        if svr.otp_auth:
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

    def has_password(self, svr):
        return bool(self._get_password_mode(svr))

    def has_pin(self):
        return self.pin and settings.user.pin_mode != PIN_DISABLED

    def _get_key_info_str(self, svr, conf_hash, include_sync_keys):
        data = {
            'version': CLIENT_CONF_VER,
            'user': self.name,
            'organization': self.org.name,
            'server': svr.name,
            'user_id': str(self.id),
            'organization_id': str(self.org.id),
            'server_id': str(svr.id),
            'sync_hosts': svr.get_sync_remotes(),
            'sync_hash': conf_hash,
            'password_mode': self._get_password_mode(svr),
        }

        if include_sync_keys:
            data['sync_token'] = self.sync_token
            data['sync_secret'] = self.sync_secret

        return '#' + json.dumps(data, indent=1).replace('\n', '\n#')

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
        conf_hash.update(self.name.encode('utf-8'))
        conf_hash.update(self.org.name.encode('utf-8'))
        conf_hash.update(svr.name.encode('utf-8'))
        conf_hash.update(svr.protocol)
        for key_remote in sorted(key_remotes):
            conf_hash.update(key_remote)
        conf_hash.update(CIPHERS[svr.cipher])
        conf_hash.update(str(svr.lzo_compression))
        conf_hash.update(str(svr.otp_auth))
        conf_hash.update(JUMBO_FRAMES[svr.jumbo_frames])
        conf_hash.update(ca_certificate)
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
        )

        if svr.lzo_compression != ADAPTIVE:
            client_conf += 'comp-lzo no\n'

        if self.has_password(svr):
            client_conf += 'auth-user-pass\n'

        if svr.tls_auth:
            client_conf += 'key-direction 1\n'

        client_conf += JUMBO_FRAMES[svr.jumbo_frames]
        client_conf += '<ca>\n%s\n</ca>\n' % ca_certificate
        if include_user_cert:
            if svr.tls_auth:
                client_conf += '<tls-auth>\n%s\n</tls-auth>\n' % (
                    svr.tls_auth_key)

            client_conf += '<cert>\n%s\n</cert>\n' % certificate
            client_conf += '<key>\n%s\n</key>\n' % private_key

        return file_name, client_conf, conf_hash

    def _generate_onc(self, svr):
        if not svr.primary_organization or \
                not svr.primary_user:
            svr.create_primary_user()

        file_name = '%s_%s_%s.onc' % (
            self.org.name, self.name, svr.name)

        conf_hash = hashlib.md5()
        conf_hash.update(str(self.org_id))
        conf_hash.update(str(self.id))
        conf_hash = '{%s}' % conf_hash.hexdigest()

        host, port = svr.get_onc_host()
        if not host:
            return None, None

        ca_certs = svr.ca_certificate_list

        tls_auth = ''
        if svr.tls_auth:
            for line in svr.tls_auth_key.split('\n'):
                if line.startswith('#'):
                    continue
                tls_auth += line + '\\n'
            tls_auth = '\n        "TLSAuthContents": "%s",' % tls_auth
            tls_auth = '\n        "KeyDirection": "1",' + tls_auth

        certs = ""
        cert_ids = []

        for cert in ca_certs:
            cert_id = '{%s}' % hashlib.md5(cert).hexdigest()
            cert_ids.append(cert_id)
            certs += OVPN_ONC_CA_CERT % (
                cert_id,
                cert,
            )

        client_ref = ''
        for cert_id in cert_ids:
            client_ref += '            "%s",\n' % cert_id
        client_ref = client_ref[:-2]

        server_ref = ''
        for cert_id in cert_ids:
            server_ref += '          "%s",\n' % cert_id
        server_ref = server_ref[:-2]

        password_mode = self._get_password_mode(svr)
        if password_mode == 'otp':
            auth = OVPN_ONC_AUTH_OTP % self.id
        elif password_mode:
            auth = OVPN_ONC_AUTH_PASS % self.id
        else:
            auth = OVPN_ONC_AUTH_NONE % self.id

        onc_conf = OVPN_ONC_CLIENT_CONF % (
            conf_hash,
            '%s - %s (%s)' % (self.name, self.org.name, svr.name),
            host,
            HASHES[svr.hash],
            ONC_CIPHERS[svr.cipher],
            client_ref,
            'adaptive' if svr.lzo_compression == ADAPTIVE else 'false',
            port,
            svr.protocol,
            server_ref,
            tls_auth,
            auth,
            certs,
        )

        return file_name, onc_conf

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
                        os.chmod(server_conf_path, 0600)
                        ovpn_conf.write(client_conf)
                    tar_file.add(server_conf_path, arcname=conf_name)
                    os.remove(server_conf_path)
            finally:
                tar_file.close()

            with open(key_archive_path, 'r') as archive_file:
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
                        os.chmod(server_conf_path, 0600)
                        ovpn_conf.write(client_conf)
                    zip_file.write(server_conf_path, arcname=conf_name)
                    os.remove(server_conf_path)
            finally:
                zip_file.close()

            with open(key_archive_path, 'r') as archive_file:
                key_archive = archive_file.read()
        finally:
            utils.rmtree(temp_path)

        return key_archive

    def build_onc_archive(self):
        temp_path = utils.get_temp_path()
        key_archive_path = os.path.join(temp_path, '%s.zip' % self.id)

        try:
            os.makedirs(temp_path)
            zip_file = zipfile.ZipFile(key_archive_path, 'w')
            try:
                user_cert_path = os.path.join(temp_path, '%s.crt' % self.id)
                user_key_path = os.path.join(temp_path, '%s.key' % self.id)
                user_p12_path = os.path.join(temp_path, '%s.p12' % self.id)

                with open(user_cert_path, 'w') as user_cert:
                    user_cert.write(self.certificate)

                with open(user_key_path, 'w') as user_key:
                    os.chmod(user_key_path, 0600)
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

                zip_file.write(user_p12_path, arcname='%s.p12' % self.name)

                os.remove(user_cert_path)
                os.remove(user_key_path)
                os.remove(user_p12_path)

                for svr in self.iter_servers():
                    server_conf_path = os.path.join(temp_path,
                        '%s_%s.onc' % (self.id, svr.id))
                    conf_name, client_conf = self._generate_onc(svr)
                    if not client_conf:
                        continue

                    with open(server_conf_path, 'w') as ovpn_conf:
                        ovpn_conf.write(client_conf)
                    zip_file.write(server_conf_path, arcname=conf_name)
                    os.remove(server_conf_path)
            finally:
                zip_file.close()

            with open(key_archive_path, 'r') as archive_file:
                key_archive = archive_file.read()
        finally:
            utils.rmtree(temp_path)

        return key_archive

    def build_key_conf(self, server_id, include_user_cert=True):
        svr = self.org.get_by_id(server_id)
        if not svr.check_groups(self.groups):
            raise UserNotInServerGroups('User not in server groups')

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
        except UserNotInServerGroups:
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

        test_hash = base64.b64encode(hash_func(pin_salt, test_pin))
        return test_hash == pin_hash

    def set_pin(self, pin):
        if not pin:
            changed = bool(self.pin)
            self.pin = None
            return changed

        changed = not self.check_pin(pin)
        self.pin = auth.generate_hash_pin_v2(pin)
        return changed

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

        network = str(ipaddress.IPNetwork(network))

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

    def audit_event(self, event_type, event_msg, remote_addr=None):
        if settings.app.auditing != ALL:
            return

        self.audit_collection.insert({
            'user_id': self.id,
            'org_id': self.org_id,
            'timestamp': utils.now(),
            'type': event_type,
            'remote_addr': remote_addr,
            'message': event_msg,
        })

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
