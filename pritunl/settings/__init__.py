from pritunl.settings.settings import Settings

from pritunl.settings.app import SettingsApp
from pritunl.settings.conf import SettingsConf
from pritunl.settings.local import SettingsLocal
from pritunl.settings.mongo import SettingsMongo
from pritunl.settings.user import SettingsUser
from pritunl.settings.vpn import SettingsVpn

import sys

app = SettingsApp
conf = SettingsConf
local = SettingsLocal
mongo = SettingsMongo
user = SettingsUser
vpn = SettingsVpn

def commit():
    pass

sys.modules[__name__] = Settings()
