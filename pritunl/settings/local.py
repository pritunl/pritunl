from pritunl.settings.group_local import SettingsGroupLocal

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

import threading

server_start = threading.Event()
server_start.set()

class SettingsLocal(SettingsGroupLocal):
    group = 'local'
    fields = {
        'quiet': False,
        'public_ip': None,
        'server_ready': threading.Event(),
        'server_start': server_start,
        'host_ping_timestamp': None,
        'sub_active': False,
        'sub_status': None,
        'sub_plan': None,
        'sub_amount': None,
        'sub_period_end': None,
        'sub_cancel_at_period_end': None,
        'sub_styles': {},
    }
