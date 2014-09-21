from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings_group import SettingsGroup

class SettingsTest(SettingsGroup):
    group = 'test'
    fields = {
        'option': 'default',
    }
