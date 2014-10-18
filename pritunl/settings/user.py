from pritunl.settings.group_mongo import SettingsGroupMongo

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

class SettingsUser(SettingsGroupMongo):
    group = 'user'
    fields = {
        'otp_secret_len': 16,
        'cert_key_bits': 4096,
        'otp_cache_ttl': 43200,
        'page_count': 10,
    }
