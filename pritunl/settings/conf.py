from pritunl.settings.group_file import SettingsGroupFile

from pritunl import conf_path

class SettingsConf(SettingsGroupFile):
    group = 'conf'
    path = conf_path
    fields = {
        'host_id': None,
        'ssl': True,
        'static_cache': True,
        'port': 443,
        'internal_port': 9755,
        'pooler': True,
        'temp_path': '/tmp/pritunl',
        'log_path': '/var/log/pritunl.log',
        'journal_path': '/var/log/pritunl_journal.log',
        'www_path': '/usr/share/pritunl/www',
        'var_run_path': '/var/run',
        'uuid_path': '/var/lib/pritunl/pritunl.uuid',
        'se_host_key_path': '/var/lib/pritunl/pritunl_se_host.key',
        'se_init_path': '/var/lib/pritunl/pritunl_se_init.json',
        'se_secret_path': '/var/lib/pritunl/pritunl_se_secret.json',
        'setup_key_path': '/var/lib/pritunl/setup_key',
        'bind_addr': '0.0.0.0',
        'mongodb_uri': 'mongodb://localhost:27017/pritunl',
        'mongodb_collection_prefix': None,
        'mongodb_read_preference': None,
        'mongodb_max_pool_size': None,
        'local_address_interface': 'auto',
    }
    commit_fields = {
        'static_cache',
        'bind_addr',
        'port',
        'log_path',
        'www_path',
        'temp_path',
        'local_address_interface',
        'mongodb_uri',
    }
