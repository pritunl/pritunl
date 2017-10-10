from pritunl.settings.group_base import SettingsGroupBase

from pritunl.constants import *

class SettingsGroupMongo(SettingsGroupBase):
    type = GROUP_MONGO

    def __init__(self):
        self.changed = set()
        self.unseted = set()

    def __setattr__(self, name, value):
        if name != 'fields' and name in self.fields:
            self.changed.add(name)
        object.__setattr__(self, name, value)

    def unset(self, name):
        self.unseted.add(name)
        try:
            delattr(self, name)
        except AttributeError:
            pass

    def get_commit_doc(self, init):
        doc = {
            '_id': self.group,
        }

        for field in self.changed:
            doc[field] = getattr(self, field)

        self.changed = set()

        if init or len(doc) > 1:
            return doc

    def get_commit_unset_doc(self):
        doc = {
            '_id': self.group,
        }

        for field in self.unseted:
            doc[field] = ""

        self.unseted = set()

        if len(doc) > 1:
            return doc
