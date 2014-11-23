from pritunl.settings.group_mongo import SettingsGroupMongo

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

class SettingsVpn(SettingsGroupMongo):
    group = 'vpn'
    fields = {
        'peer_limit': 300,
        'peer_limit_timeout': 10,
        'default_dh_param_bits': 1536,
        'cache_otp_codes': True,
        'log_lines': 5000,
        'server_ping': 3,
        'server_ping_ttl': 6,
        'status_update_rate': 3,
        'http_request_timeout': 10,
        'op_timeout': 4,
        'bandwidth_update_rate': 15,
        'safe_pub_subnets': ['50.203.224.0/24'],
    }
