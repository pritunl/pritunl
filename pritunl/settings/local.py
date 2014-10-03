from pritunl.settings.group_local import SettingsGroupLocal

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

class SettingsLocal(SettingsGroupLocal):
    group = 'local'
    fields = {
        'public_ip': None,
    }
