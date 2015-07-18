from pritunl.settings.group_base import SettingsGroupBase

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

class SettingsGroupLocal(SettingsGroupBase):
    type = GROUP_LOCAL
