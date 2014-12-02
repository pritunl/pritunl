from pritunl.settings.group_file import SettingsGroupFile

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import conf_path

class SettingsConf(SettingsGroupFile):
    group = 'conf'
    path = conf_path
    fields = {
        'debug': False,
        'ssl': True,
        'static_cache': True,
        'port': 9700,
        'pooler': True,
        'temp_path': 'tmp/pritunl',
        'log_path': '/var/log/pritunl.log',
        'www_path': '/usr/share/pritunl/www',
        'var_run_path': '/var/run',
        'uuid_path': '/var/lib/pritunl/pritunl.uuid',
        'server_cert_path': '/var/lib/pritunl/pritunl.crt',
        'server_key_path': '/var/lib/pritunl/pritunl.key',
        'bind_addr': '0.0.0.0',
        'mongodb_uri': 'mongodb://localhost:27017/pritunl',
        'mongodb_collection_prefix': None,
        'local_address_interface': 'auto',
        'data_path': '/var/lib/pritunl', # For 0.10.x upgrade
        'db_path': '/var/lib/pritunl/pritunl.db', # For 0.10.x upgrade
    }
    commit_fields = {
        'debug',
        'static_cache',
        'bind_addr',
        'port',
        'log_path',
        'www_path',
        'temp_path',
        'server_cert_path',
        'server_key_path',
        'local_address_interface',
        'mongodb_uri',
    }
