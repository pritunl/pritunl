from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import utils
from pritunl import queue
from pritunl import logger
from pritunl import messenger

import tarfile
import os
import subprocess
import hashlib
import base64
import struct
import hmac
import json
import uuid

class User(mongo.MongoObject):
    fields = {
        'org_id',
        'name',
        'email',
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
    }
    fields_default = {
        'name': 'undefined',
        'disabled': False,
        'type': CERT_CLIENT,
        'auth_type': LOCAL_AUTH,
    }

    def __init__(self, org, name=None, email=None, type=None, auth_type=None,
            disabled=None, resource_id=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        self.org = org
        self.org_id = org.id

        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if type is not None:
            self.type = type
        if auth_type is not None:
            self.auth_type = auth_type
        if disabled is not None:
            self.disabled = disabled
        if resource_id is not None:
            self.resource_id = resource_id

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('users')

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
            'type': self.type,
            'otp_secret': self.otp_secret,
            'disabled': self.disabled,
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
        self.unassign_ip_addr()
        mongo.MongoObject.remove(self)

    def disconnect(self):
        messenger.publish('instance', ['user_disconnect', self.id])

    def auth_check(self):
        if self.auth_type == GOOGLE_AUTH:
            try:
                resp = utils.request.get(AUTH_SERVER +
                    '/update/google?user=%s&license=%s' % (
                        self.email, settings.app.license))

                if resp.status_code == 200:
                    return True
            except:
                logger.exception('Google auth check error', 'user',
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
        for server in self.org.iter_servers(fields=(
                'id', 'network', 'network_start',
                'network_end', 'network_lock')):
            server.assign_ip_addr(self.org.id, self.id)

    def unassign_ip_addr(self):
        for server in self.org.iter_servers(fields=(
                'id', 'network', 'network_start',
                'network_end', 'network_lock')):
            server.unassign_ip_addr(self.org.id, self.id)

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

    def _get_key_info_str(self, server, conf_hash):
        return '#' + json.dumps({
            'version': CLIENT_CONF_VER,
            'user': self.name,
            'organization': self.org.name,
            'server': server.name,
            'user_id': str(self.id),
            'organization_id': str(self.org.id),
            'server_id': str(server.id),
            'sync_token': self.sync_token,
            'sync_secret': self.sync_secret,
            'sync_hash': conf_hash,
            'sync_hosts': server.get_sync_remotes(),
        }, indent=1).replace('\n', '\n#')

    def _generate_conf(self, server, include_user_cert=True):
        if not self.sync_token or not self.sync_secret:
            self.sync_token = utils.generate_secret()
            self.sync_secret = utils.generate_secret()
            self.commit(('sync_token', 'sync_secret'))

        file_name = '%s_%s_%s.ovpn' % (
            self.org.name, self.name, server.name)
        if not server.ca_certificate:
            server.generate_ca_cert()
        key_remotes = server.get_key_remotes()
        ca_certificate = server.ca_certificate
        certificate = utils.get_cert_block(self.certificate)
        private_key = self.private_key.strip()

        conf_hash = hashlib.md5()
        conf_hash.update(self.name.encode('utf-8'))
        conf_hash.update(self.org.name.encode('utf-8'))
        conf_hash.update(server.name.encode('utf-8'))
        conf_hash.update(server.protocol)
        for key_remote in sorted(key_remotes):
            conf_hash.update(key_remote)
        conf_hash.update(CIPHERS[server.cipher])
        conf_hash.update(str(server.lzo_compression))
        conf_hash.update(str(server.otp_auth))
        conf_hash.update(JUMBO_FRAMES[server.jumbo_frames])
        conf_hash.update(ca_certificate)
        conf_hash = conf_hash.hexdigest()

        client_conf = OVPN_INLINE_CLIENT_CONF % (
            self._get_key_info_str(server, conf_hash),
            uuid.uuid4().hex,
            utils.random_name(),
            server.adapter_type,
            server.adapter_type,
            server.protocol,
            server.get_key_remotes(),
            CIPHERS[server.cipher],
            server.ping_interval,
            server.ping_timeout,
        )

        if server.lzo_compression != ADAPTIVE:
            client_conf += 'comp-lzo no\n'

        if server.otp_auth:
            client_conf += 'auth-user-pass\n'

        if server.tls_auth:
            client_conf += 'key-direction 1\n'

        client_conf += JUMBO_FRAMES[server.jumbo_frames]
        client_conf += '<ca>\n%s\n</ca>\n' % ca_certificate
        if include_user_cert:
            if server.tls_auth:
                client_conf += '<tls-auth>\n%s\n</tls-auth>\n' % (
                    server.tls_auth_key)

            client_conf += '<cert>\n%s\n</cert>\n' % certificate
            client_conf += '<key>\n%s\n</key>\n' % private_key

        return file_name, client_conf, conf_hash

    def build_key_archive(self):
        temp_path = utils.get_temp_path()
        key_archive_path = os.path.join(temp_path, '%s.tar' % self.id)

        try:
            os.makedirs(temp_path)
            tar_file = tarfile.open(key_archive_path, 'w')
            try:
                for server in self.org.iter_servers():
                    server_conf_path = os.path.join(temp_path,
                        '%s_%s.ovpn' % (self.id, server.id))
                    conf_name, client_conf, conf_hash = self._generate_conf(
                        server)

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

    def build_key_conf(self, server_id, include_user_cert=True):
        server = self.org.get_by_id(server_id)
        conf_name, client_conf, conf_hash = self._generate_conf(server,
            include_user_cert)

        return {
            'name': conf_name,
            'conf': client_conf,
            'hash': conf_hash,
        }

    def sync_conf(self, server_id, conf_hash):
        key = self.build_key_conf(server_id, False)

        if key['hash'] != conf_hash:
            return key

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
