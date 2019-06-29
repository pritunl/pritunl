from pritunl.constants import *
from pritunl.settings.group_mongo import SettingsGroupMongo

class SettingsUser(SettingsGroupMongo):
    group = 'user'
    fields = {
        'audit_limit': 2500,
        'gravatar': True,
        'otp_secret_len': 16,
        'pin_mode': PIN_OPTIONAL,
        'pin_min_length': 6,
        'pin_digits_only': True,
        'reconnect': True,
        'force_password_mode': None,
        'password_encryption': True,
        'cert_key_bits': 4096,
        'cert_message_digest': 'sha256',
        'page_count': 10,
        'skip_remote_sso_check': False,
        'conf_sync': True,
        'restrict_import': False,
    }
