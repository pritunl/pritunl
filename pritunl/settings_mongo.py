from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings_group import SettingsGroup

class SettingsMongo(SettingsGroup):
    group = 'mongo'
    fields = {
        'tran_max_attempts': 6,
        'tran_ttl': 10,
        'queue_max_attempts': 3,
        'queue_ttl': 15,
        'task_max_attempts': 3,
        'task_ttl': 30,
    }
