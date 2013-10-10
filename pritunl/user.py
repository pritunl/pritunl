from constants import *
from pritunl import app_server, openssl_lock
from config import Config
from log_entry import LogEntry
from event import Event
import uuid
import tarfile
import os
import subprocess
import logging

logger = logging.getLogger(APP_NAME)

class User(Config):
    str_options = ['name']

    def __init__(self, org, id=None, name=None, type=None):
        Config.__init__(self)
        self.org = org
        self.id = id

        if type is not None:
            self.type = type

        if self.id is None:
            if type == CERT_CA:
                self.id = CA_CERT_ID
            elif type is None:
                raise AttributeError('Type must be specified')
            else:
                self.id = uuid.uuid4().hex
            self._initialized = False
        else:
            self._initialized = True

        self.reqs_path = os.path.join(self.org.path, REQS_DIR,
            '%s.csr' % self.id)
        self.ssl_conf_path = os.path.join(self.org.path, TEMP_DIR,
            '%s.conf' % self.id)
        self.key_path = os.path.join(self.org.path, KEYS_DIR,
            '%s.key' % self.id)
        self.cert_path = os.path.join(self.org.path, CERTS_DIR,
            '%s.crt' % self.id)
        self.key_archive_path = os.path.join(self.org.path,
            TEMP_DIR, '%s.tar' % self.id)
        self.set_path(os.path.join(self.org.path, USERS_DIR,
            '%s.conf' % self.id))

        if name is not None:
            self.name = name

        if not self._initialized:
            self._initialize()

    def __getattr__(self, name):
        if name == 'type':
            self.type = self._load_type()
            return self.type
        return Config.__getattr__(self, name)

    def _initialize(self):
        self._create_ssl_conf()
        self._cert_request()
        self.commit()
        self._cert_create()
        self._delete_ssl_conf()
        LogEntry(message='Created new user.')
        Event(type=USERS_UPDATED)

    def _cert_request(self):
        openssl_lock.acquire()
        try:
            args = [
                'openssl', 'req', '-new', '-batch',
                '-config', self.ssl_conf_path,
                '-out', self.reqs_path,
                '-keyout', self.key_path,
                '-reqexts', '%s_req_ext' % self.type,
            ]
            subprocess.check_call(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to create user cert requests. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
            })
            raise
        finally:
            openssl_lock.release()
        os.chmod(self.key_path, 0600)

    def _cert_create(self):
        openssl_lock.acquire()
        try:
            args = ['openssl', 'ca', '-batch']
            if self.type == CERT_CA:
                args += ['-selfsign']
            args += [
                '-config', self.ssl_conf_path,
                '-in', self.reqs_path,
                '-out', self.cert_path,
                '-extensions', '%s_ext' % self.type,
            ]
            subprocess.check_call(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to create user cert. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
            })
            raise
        finally:
            openssl_lock.release()

    def _create_ssl_conf(self):
        conf_data = CERT_CONF % (self.org.id, self.org.path,
            app_server.key_bits or DEFAULT_KEY_BITS, self.id)
        with open(self.ssl_conf_path, 'w') as conf_file:
            conf_file.write(conf_data)

    def _delete_ssl_conf(self):
        os.remove(self.ssl_conf_path)

    def _load_type(self):
        with open(self.cert_path, 'r') as cert_file:
            cert_data = cert_file.read()
            if 'CA:TRUE' in cert_data:
                return CERT_CA
            elif 'TLS Web Server Authentication' in cert_data:
                return CERT_SERVER
            else:
                return  CERT_CLIENT

    def _revoke(self, reason):
        if self.id == CA_CERT_ID:
            raise TypeError('Cannot revoke ca cert')

        if not os.path.isfile(self.cert_path):
            logger.warning('Skipping revoke of non existent user. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
            })
            return

        openssl_lock.acquire()
        try:
            self._create_ssl_conf()
            args = ['openssl', 'ca', '-batch',
                '-config', self.ssl_conf_path,
                '-revoke', self.cert_path,
                '-crl_reason', reason
            ]
            proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            returncode = proc.wait()
            if returncode != 0:
                err_output = proc.communicate()[1]
                if 'ERROR:Already revoked' not in err_output:
                    raise subprocess.CalledProcessError(returncode, args)
            self._delete_ssl_conf()
        except subprocess.CalledProcessError:
            logger.exception('Failed to revoke user cert. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
            })
            raise
        finally:
            openssl_lock.release()
        self.org.generate_crl()

    def build_key_archive(self):
        user_key_arcname = '%s_%s.key' % (self.org.name, self.name)
        user_cert_arcname = '%s_%s.crt' % (self.org.name, self.name)

        tar_file = tarfile.open(self.key_archive_path, 'w')
        try:
            tar_file.add(self.key_path, arcname=user_key_arcname)
            tar_file.add(self.cert_path, arcname=user_cert_arcname)
            for server in self.org.get_servers():
                server_cert_arcname = '%s_%s_%s.crt' % (
                    self.org.name, self.name, server.name)
                server_conf_path = os.path.join(self.org.path,
                    TEMP_DIR, '%s_%s.ovpn' % (self.id, server.id))
                server_conf_arcname = '%s_%s_%s.ovpn' % (
                    self.org.name, self.name, server.name)
                server.generate_ca_cert()
                tar_file.add(server.ca_cert_path, arcname=server_cert_arcname)

                with open(server_conf_path, 'w') as ovpn_conf:
                    ovpn_conf.write(OVPN_CLIENT_CONF % (
                        server.protocol,
                        server.public_address, server.port,
                        server_cert_arcname,
                        user_cert_arcname,
                        user_key_arcname,
                    ))
                tar_file.add(server_conf_path, arcname=server_conf_arcname)
                os.remove(server_conf_path)
        finally:
            tar_file.close()

        return self.key_archive_path

    def rename(self, name):
        self.name = name
        self.commit()
        Event(type=USERS_UPDATED)

    def remove(self, reason=UNSPECIFIED):
        self._revoke(reason)

        try:
            os.remove(self.reqs_path)
        except OSError, error:
            logger.debug('Failed to remove user reqs file. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
                'path': self.reqs_path,
                'error': error,
            })

        try:
            os.remove(self.ssl_conf_path)
        except OSError, error:
            pass

        try:
            os.remove(self.key_path)
        except OSError, error:
            logger.debug('Failed to remove user key file. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
                'path': self.reqs_path,
                'error': error,
            })

        try:
            os.remove(self.cert_path)
        except OSError, error:
            logger.debug('Failed to remove user cert file. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
                'path': self.reqs_path,
                'error': error,
            })

        try:
            os.remove(self.get_path())
        except OSError, error:
            logger.debug('Failed to remove user conf file. %r' % {
                'org_id': self.org.id,
                'user_id': self.id,
                'path': self.reqs_path,
                'error': error,
            })

        Event(type=USERS_UPDATED)
        LogEntry(message='Deleted user.')
