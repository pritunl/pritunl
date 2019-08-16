from pritunl.settings.group_local import SettingsGroupLocal

import threading

server_start = threading.Event()
server_start.set()

class SettingsLocal(SettingsGroupLocal):
    group = 'local'
    fields = {
        'se_host_key': None,
        'se_authorize_key': None,
        'se_encryption_key': None,
        'se_client_key': None,
        'se_client_pub_key': None,
        'quiet': False,
        'public_ip': None,
        'public_ip6': None,
        'server_ready': threading.Event(),
        'server_start': server_start,
        'host_ping_timestamp': None,
        'ntp_time': None,
        'sub_active': False,
        'sub_status': None,
        'sub_plan': None,
        'sub_amount': None,
        'sub_period_end': None,
        'sub_trial_end': None,
        'sub_cancel_at_period_end': None,
        'sub_balance': None,
        'sub_url_key': False,
        'sub_styles': {},
    }
