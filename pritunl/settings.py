from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings_test import SettingsTest
import pritunl.mongo as mongo

class Settings(object):
    @cached_static_property
    def collection(cls):
        return mongo.get_collection('system')

    @cached_property
    def test(self):
        return SettingsTest()

    def commit(self, all_fields=False):
        docs = []

        for group in dir(self):
            if group[0] == '_' or group in SETTINGS_RESERVED:
                continue
            docs.append(getattr(self, group).get_commit_doc(all_fields))
