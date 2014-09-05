from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.system_conf import SystemConf
from pritunl.mongo_object import MongoObject
import pritunl.mongo as mongo

class Settings(SystemConf):
    fields = {
        'email_from': ('email', 'from_addr'),
        'email_api_key': ('email', 'api_key'),
    }

    def __getattr__(self, name):
        if name in self.fields:
            return self.get(*self.fields[name])
        if name not in self.__dict__:
            raise AttributeError(
                'Settings instance has no attribute %r' % name)
        return self.__dict__[name]

    def dict(self):
        data = {}
        for field in self.fields:
            data[field] = self.get(*self.fields[field])
        return data
