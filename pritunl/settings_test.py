from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings_group import SettingsGroup, add_to_settings

@add_to_settings
class SettingsTest(SettingsGroup):
    group = 'test'
    fields = {
        'option': 'default',
    }
