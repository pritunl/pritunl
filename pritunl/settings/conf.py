from pritunl.settings.group_file import SettingsGroupFile

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

class SettingsConf(SettingsGroupFile):
    group = 'conf'
    path = 'test.conf'
    fields = {
        'debug': False,
        'ssl': True,
        'static_cache': True,
        'port': 9700,
        'pooler': True,
        'temp_path': 'tmp/pritunl',
        'log_path': '/var/log/pritunl.log',
        'www_path': '/usr/share/pritunl/www',
        'server_cert_path': '/etc/pritunl.crt',
        'server_key_path': '/etc/pritunl.key',
        'bind_addr': '0.0.0.0',
        'mongodb_url': 'mongodb://localhost:27017/pritunl',
        'mongodb_collection_prefix': None,
    }
