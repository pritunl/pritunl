from pritunl.settings.group_local import SettingsGroupLocal

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

class SettingsLocal(SettingsGroupLocal):
    group = 'local'
    fields = {
        'public_ip': None,
        'host_ping_timestamp': None,
    }
