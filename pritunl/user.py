from constants import *
from exceptions import *
from pritunl import app_server
from cache import cache_db
from cache_trie import CacheTrie
from log_entry import LogEntry
from event import Event
from system_conf import SystemConf
from mongo_object import MongoObject
import mongo
import uuid
import tarfile
import os
import subprocess
import logging
import hashlib
import base64
import utils
import struct
import hmac
import time
import threading
import json

logger = logging.getLogger(APP_NAME)

class User(MongoObject):
    fields = {
        'org_id',
        'name',
        'email',
        'otp_secret',
        'type',
        'disabled',
        'private_key',
        'certificate',
    }
    fields_default = {
        'name': 'undefined',
        'disabled': False,
    }

    def __init__(self, org, name=None, email=None, type=None, **kwargs):
        MongoObject.__init__(self, **kwargs)

        self.org = org
        self.org_id = org.id
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if type is not None:
            self.type = type

    @staticmethod
    def get_collection():
        return mongo.get_collection('users')

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
        temp_path = app_server.get_temp_path()
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
                    CERT_KEY_BITS,
                    self.org.id,
                    self.id,
                    index_path,
                    serial_path,
                    temp_path,
                    ca_cert_path,
                    ca_key_path,
                ))

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
                subprocess.check_call(args, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
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
                subprocess.check_call(args, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as exception:
                logger.exception('Failed to create user cert. %r' % {
                    'org_id': self.org.id,
                    'user_id': self.id,
                    'output': exception.output,
                })
                raise
            self.read_file('certificate', cert_path)
        finally:
            utils.rmtree(temp_path)

    def get_cache_key(self, suffix=None):
        if not self.cache_prefix:
            raise AttributeError('Cached config object requires cache_prefix')
        key = self.cache_prefix + '-' + self.org.id + '_' + self.id
        if suffix:
            key += '-%s' % suffix
        return key

    def generate_otp_secret(self):
        sha_hash = hashlib.sha512()
        sha_hash.update(os.urandom(8192))
        byte_hash = sha_hash.digest()
        for i in xrange(6):
            sha_hash = hashlib.sha512()
            sha_hash.update(byte_hash)
            byte_hash = sha_hash.digest()
        self.otp_secret = base64.b32encode(byte_hash)[:DEFAULT_OTP_SECRET_LEN]

    def verify_otp_code(self, code, remote_ip=None):
        if remote_ip:
            otp_cache = cache_db.get(self.get_cache_key('otp_cache'))
            if otp_cache:
                cur_code, cur_remote_ip = otp_cache.split(',')
                if cur_code == code and cur_remote_ip == remote_ip:
                    cache_db.expire(self.get_cache_key('otp_cache'),
                        OTP_CACHE_TTL)
                    return True
                else:
                    cache_db.remove(self.get_cache_key('otp_cache'))

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

        used_codes = cache_db.dict_get_all(self.get_cache_key('otp'))
        for auth_time, used_code in used_codes.items():
            if int(time.time()) - int(auth_time) > 120:
                cache_db.dict_remove(self.get_cache_key('otp'), auth_time)
            if used_code == code:
                return False

        cache_db.dict_set(self.get_cache_key('otp'),
            str(int(time.time())), code)
        cache_db.expire(self.get_cache_key('otp_cache'), OTP_CACHE_TTL)
        cache_db.set(self.get_cache_key('otp_cache'),
            ','.join((code, remote_ip)))
        return True

    def _get_key_info_str(self, user_name, org_name, server_name):
        return json.dumps({
            'version': CLIENT_CONF_VER,
            'user': user_name,
            'organization': org_name,
            'server': server_name,
        })

    def build_key_archive(self):
        temp_path = app_server.get_temp_path()
        key_archive_path = os.path.join(temp_path, '%s.tar' % self.id)

        try:
            os.makedirs(temp_path)
            tar_file = tarfile.open(key_archive_path, 'w')
            try:
                for server in self.org.iter_servers():
                    server_conf_path = os.path.join(self.org.path,
                        TEMP_DIR, '%s_%s.ovpn' % (self.id, server.id))
                    server_conf_arcname = '%s_%s_%s.ovpn' % (
                        self.org.name, self.name, server.name)
                    server.generate_ca_cert()

                    client_conf = OVPN_INLINE_CLIENT_CONF % (
                        self._get_key_info_str(
                            self.name, self.org.name, server.name),
                        server.protocol,
                        server.public_address, server.port,
                    )

                    if server.otp_auth:
                        client_conf += 'auth-user-pass\n'

                    client_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
                        server.ca_cert_path)
                    client_conf += '<cert>\n%s\n' + \
                        '</cert>\n' % utils.get_cert_block(self.cert_path)
                    client_conf += '<key>\n%s\n</key>\n' % open(
                        self.key_path).read().strip()

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
            server.public_address, server.port,
        )

        if server.otp_auth:
            client_conf += 'auth-user-pass\n'

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
        settings = SystemConf()

        if not settings.email_from_addr or not settings.email_api_key:
            raise EmailNotConfiguredError('Email not configured', {
                'org_id': self.org.id,
                'user_id': self.id,
            })

        key_link = self.org.create_user_key_link(self.id)
        response = utils.request.post(POSTMARK_SERVER,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': settings.email_api_key,
            },
            json_data={
                'From': settings.email_from_addr,
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

    @classmethod
    def get_user(cls, org, id):
        return cls(org=org, id=id)

    @classmethod
    def find_user(cls, org, name=None, type=None):
        spec = {
            'org_id': org.id,
        }
        if name is not None:
            spec['name'] = name
        if type is not None:
            spec['type'] = type
        return cls(org, spec=spec)
