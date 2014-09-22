from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings_group import SettingsGroup

class SettingsUser(SettingsGroup):
    group = 'user'
    fields = {
        'otp_secret_len': 16,
        'cert_key_bits': 4096,
        'otp_cache_ttl': 43200,
        'page_count': 10,
    }
