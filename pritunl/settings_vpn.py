from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings_group import SettingsGroup

class SettingsVpn(SettingsGroup):
    group = 'vpn'
    fields = {
        'default_dh_param_bits': 1536,
        'log_lines': 1024,
        'status_update_rate': 5,
        'http_request_timeout': 10,
        'safe_pub_subnets': ['50.203.224.0/24'],
    }
