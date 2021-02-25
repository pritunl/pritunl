from pritunl.settings.group_base import SettingsGroupBase

from pritunl.constants import *

import json
import os

class SettingsGroupFile(SettingsGroupBase):
    type = GROUP_FILE
    path = None
    commit_fields = set()

    def load(self):
        if not os.path.isfile(self.path):
            return

        with open(self.path, 'r') as settings_file:
            doc = json.loads(settings_file.read())

        for field, value in list(doc.items()):
            setattr(self, field, value)

    def commit(self):
        doc = {}

        for field, default in self.fields.items():
            if hasattr(self, field):
                value = getattr(self, field)
                if field in self.commit_fields or value != default:
                    doc[field] = getattr(self, field)

        with open(self.path, 'w') as settings_file:
            settings_file.write(json.dumps(doc, indent=4))
