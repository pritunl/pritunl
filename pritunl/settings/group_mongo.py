from pritunl.settings.group_base import SettingsGroupBase

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

class SettingsGroupMongo(SettingsGroupBase):
    type = GROUP_MONGO

    def __init__(self):
        self.changed = set()

    def __setattr__(self, name, value):
        if name != 'fields' and name in self.fields:
            self.changed.add(name)
        object.__setattr__(self, name, value)

    def get_commit_doc(self, all_fields):
        doc = {
            '_id': self.group,
        }

        for field in self.fields if all_fields else self.changed:
            doc[field] = getattr(self, field)

        if len(doc) > 1:
            return doc
