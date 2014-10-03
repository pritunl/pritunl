from pritunl.settings.group_base import SettingsGroupBase

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

import json
import os

class SettingsGroupFile(SettingsGroupBase):
    type = GROUP_FILE
    path = None

    def load(self):
        if not os.path.isfile(self.path):
            return

        with open(self.path, 'r') as settings_file:
            doc = json.loads(settings_file.read())

        for field, value in doc.items():
            setattr(self, field, value)

    def commit(self):
        doc = {}

        for field in self.fields:
            if hasattr(self, field):
                doc[field] = getattr(self, field)

        with open(self.path, 'w') as settings_file:
            settings_file.write(json.dumps(doc, indent=4))
