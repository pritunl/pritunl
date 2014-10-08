from pritunl.settings.group_mongo import SettingsGroupMongo

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

class SettingsVpn(SettingsGroupMongo):
    group = 'vpn'
    fields = {
        'default_dh_param_bits': 1536,
        'log_lines': 10000,
        'status_update_rate': 3,
        'http_request_timeout': 10,
        'safe_pub_subnets': ['50.203.224.0/24'],
    }
