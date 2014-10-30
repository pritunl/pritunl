from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import app
from pritunl import mongo
from pritunl import utils
from pritunl import queue
from pritunl import logger

import tarfile
import os
import subprocess
import hashlib
import base64
import struct
import hmac
import time
import threading
import json
import bson
import random

class User(mongo.MongoObject):
    fields = {
        'org_id',
        'name',
        'email',
        'otp_secret',
        'type',
        'disabled',
        'private_key',
        'certificate',
        'resource_id',
    }
    fields_default = {
        'name': 'undefined',
        'disabled': False,
        'type': CERT_CLIENT,
    }

    def __init__(self, org, name=None, email=None, type=None, disabled=None,
            resource_id=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        self.org = org
        self.org_id = org.id

        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if type is not None:
            self.type = type
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
                serial_file.write('01\n')

            with open(ssl_conf_path, 'w') as conf_file:
                conf_file.write(CERT_CONF % (
                    settings.user.cert_key_bits,
                    self.org.id,
                    self.id,
                    index_path,
                    serial_path,
                    temp_path,
                    ca_cert_path,
                    ca_key_path,
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
                logger.exception('Failed to create user cert requests. %r' % {
                    'org_id': self.org.id,
                    'user_id': self.id,
                })
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
                logger.exception('Failed to create user cert. %r' % {
                    'org_id': self.org.id,
                    'user_id': self.id,
                })
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
            logger.exception('Failed to assign users ip address. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
            })

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

    def get_cache_key(self, suffix=None):
        if not self.cache_prefix:
            raise AttributeError('Cached config object requires cache_prefix')
        key = self.cache_prefix + '-' + self.org.id + '_' + self.id
        if suffix:
            key += '-%s' % suffix
        return key

    def assign_ip_addr(self):
        for server in self.org.iter_servers():
            server.assign_ip_addr(self.org.id, self.id)

    def unassign_ip_addr(self):
        for server in self.org.iter_servers():
            server.unassign_ip_addr(self.org.id, self.id)

    def generate_otp_secret(self):
        sha_hash = hashlib.sha512()
        sha_hash.update(os.urandom(8192))
        byte_hash = sha_hash.digest()
        for _ in xrange(6):
            sha_hash = hashlib.sha512()
            sha_hash.update(byte_hash)
            byte_hash = sha_hash.digest()
        self.otp_secret = base64.b32encode(
            byte_hash)[:settings.user.otp_secret_len]

    def verify_otp_code(self, code, remote_ip=None):
        if remote_ip:
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
        epoch = int(time.time() / 30)
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

        if remote_ip:
            self.otp_cache_collection.update({
                '_id': self.id,
            }, {'$set': {
                'otp_hash': otp_hash,
                'timestamp': utils.now(),
            }}, upsert=True)

        return True

    def _get_key_info_str(self, user_name, org_name, server_name, conf_hash):
        return json.dumps({
            'version': CLIENT_CONF_VER,
            'user': user_name,
            'organization': org_name,
            'server': server_name,
            'hash': conf_hash,
        })

    def _generate_conf(self, server):
        file_name = '%s_%s_%s.ovpn' % (
            self.org.name, self.name, server.name)
        server.generate_ca_cert()
        key_remotes = server.get_key_remotes()
        ca_certificate = utils.get_cert_block(server.ca_certificate)
        certificate = utils.get_cert_block(self.certificate)
        private_key = self.private_key.strip()

        conf_hash = hashlib.md5()
        conf_hash.update(self.name)
        conf_hash.update(self.org.name)
        conf_hash.update(server.name)
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
            self._get_key_info_str(self.name, self.org.name,
                server.name, conf_hash),
            server.protocol,
            server.get_key_remotes(),
            CIPHERS[server.cipher],
        )

        if server.lzo_compression != ADAPTIVE:
            client_conf += 'comp-lzo no\n'

        if server.otp_auth:
            client_conf += 'auth-user-pass\n'

        client_conf += JUMBO_FRAMES[server.jumbo_frames]
        client_conf += '<ca>\n%s\n</ca>\n' % ca_certificate
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
                    server_conf_arcname = '%s_%s_%s.ovpn' % (
                        self.org.name, self.name, server.name)
                    server.generate_ca_cert()

                    client_conf = OVPN_INLINE_CLIENT_CONF % (
                        self._get_key_info_str(
                            self.name, self.org.name, server.name),
                        server.protocol,
                        server.get_key_remotes(),
                        CIPHERS[server.cipher],
                    )

                    if server.lzo_compression != ADAPTIVE:
                        client_conf += 'comp-lzo no\n'

                    if server.otp_auth:
                        client_conf += 'auth-user-pass\n'

                    client_conf += JUMBO_FRAMES[server.jumbo_frames]
                    client_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
                        server.ca_certificate)
                    client_conf += ('<cert>\n%s\n' + \
                        '</cert>\n') % utils.get_cert_block(self.certificate)
                    client_conf += '<key>\n%s\n</key>\n' % (
                        self.private_key.strip())

                    with open(server_conf_path, 'w') as ovpn_conf:
                        os.chmod(server_conf_path, 0600)
                        ovpn_conf.write(client_conf)
                    tar_file.add(server_conf_path, arcname=server_conf_arcname)
                    os.remove(server_conf_path)
            finally:
                tar_file.close()

            with open(key_archive_path, 'r') as archive_file:
                key_archive = archive_file.read()
        finally:
            utils.rmtree(temp_path)

        return key_archive

    def build_key_conf(self, server_id):
        server = self.org.get_server(server_id)
        conf_name = '%s_%s_%s.ovpn' % (self.org.name, self.name, server.name)
        server.generate_ca_cert()

        client_conf = OVPN_INLINE_CLIENT_CONF % (
            self._get_key_info_str(self.name, self.org.name, server.name),
            server.protocol,
            server.get_key_remotes(),
            CIPHERS[server.cipher],
        )

        if server.lzo_compression != ADAPTIVE:
            client_conf += 'comp-lzo no\n'

        if server.otp_auth:
            client_conf += 'auth-user-pass\n'

        client_conf += PERF_MODES[server.performance_mode]
        client_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
            server.ca_certificate)
        client_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
            self.certificate)
        client_conf += '<key>\n%s\n</key>\n' % self.private_key.strip()

        return {
            'name': conf_name,
            'conf': client_conf,
        }

    def send_key_email(self, key_link_domain):
        if not settings.app.email_from_addr or not settings.app.email_api_key:
            raise EmailNotConfiguredError('Email not configured', {
                'org_id': self.org.id,
                'user_id': self.id,
            })

        key_link = self.org.create_user_key_link(self.id)
        response = utils.request.post(POSTMARK_SERVER,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': settings.app.email_api_key,
            },
            json_data={
                'From': settings.app.email_from_addr,
                'To': self.email,
                'Subject': 'Pritunl VPN Key',
                'TextBody':  'Your vpn key can be downloaded from the ' +
                    'temporary link below. You may also directly import ' +
                    'your keys in the Pritunl client using the temporary ' +
                    'URI link.\n\n' +
                    'Key Link: ' + key_link_domain + key_link['view_url'] +
                    '\nURI Key Link: ' +
                    key_link_domain.replace('http', 'pt', 1) +
                    key_link['uri_url'],
            },
        )

        # TODO Use K to view previous in git commit -p

        # TODO add uri link to view page

        # TODO
        # <script type="application/ld+json">
        # {
        #   "@context": "http://schema.org",
        #   "@type": "EmailMessage",
        #   "action": {
        #     "@type": "ViewAction",
        #     "url": "%s",
        #     "name": "View Key"
        #   },
        #   "description": "View Pritunl key and configuration information"
        # }
        # </script>

        response = response.json()
        error_code = response.get('ErrorCode')
        error_msg = response.get('Message')

        if error_code == 0:
            pass
        elif error_code == 10:
            raise EmailApiKeyInvalid('Email api key invalid', {
                'org_id': self.org.id,
                'user_id': self.id,
                'error_code': error_code,
                'error_msg': error_msg,
            })
        elif error_code == 400:
            raise EmailFromInvalid('Email from invalid', {
                'org_id': self.org.id,
                'user_id': self.id,
                'error_code': error_code,
                'error_msg': error_msg,
            })
        else:
            logger.error('Unknown send user email error. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
                'error_code': error_code,
                'error_msg': error_msg,
            })
            raise EmailError('Unknown send user email error.', {
                'org_id': self.org.id,
                'user_id': self.id,
                'error_code': error_code,
                'error_msg': error_msg,
            })
