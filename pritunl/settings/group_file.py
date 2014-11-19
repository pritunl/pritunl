from pritunl.settings.group_base import SettingsGroupBase

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

import json
import os

class SettingsGroupFile(SettingsGroupBase):
    type = GROUP_FILE
    path = None

    def load(self):
        if not os.path.isfile(self.path):
            return

        try:
            with open(self.path, 'r') as settings_file:
                doc = json.loads(settings_file.read())
        except ValueError:
            doc = {}

            with open(self.path, 'r') as settings_file:
                for line in settings_file.readlines():
                    line = line.rstrip('\n')
                    name, value = line.split('=', 1)

                    if name in ('debug', 'ssl'):
                        if value in ('true', 't', 'yes', 'y'):
                            value = True
                        elif value in ('false', 'f', 'no', 'n'):
                            value = False
                        else:
                            value = None
                        setattr(self, name, value)
                    elif name == 'port':
                        setattr(self, name, int(value))
                    elif name in ('log_path', 'www_path', 'data_path',
                            'db_path'):
                        setattr(self, name, os.path.normpath(value))
                    elif name in ('bind_addr'):
                        setattr(self, name, value)
                self.commit()

        for field, value in doc.items():
            setattr(self, field, value)

    def commit(self):
        doc = {}

        for field in self.fields:
            if hasattr(self, field):
                doc[field] = getattr(self, field)

        with open(self.path, 'w') as settings_file:
            settings_file.write(json.dumps(doc, indent=4))
