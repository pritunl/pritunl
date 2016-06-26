from pritunl.constants import *
from pritunl.settings.group_mongo import SettingsGroupMongo

class SettingsUser(SettingsGroupMongo):
    group = 'user'
    fields = {
        'audit_limit': 1000,
        'gravatar': True,
        'otp_secret_len': 16,
        'pin_mode': PIN_OPTIONAL,
        'pin_min_length': 6,
        'cert_key_bits': 4096,
        'cert_message_digest': 'sha256',
        'otp_cache_ttl': 43200,
        'page_count': 10,
        'skip_remote_sso_check': False,
    }
