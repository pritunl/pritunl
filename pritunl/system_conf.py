from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import pritunl.mongo as mongo
import collections

class SystemConf():
    def __init__(self):
        self._cached = {}
        self._changed = collections.defaultdict(dict)

    @static_property
    def collection(cls):
        return mongo.get_collection('system')

    def _load_doc(self, group):
        doc = self.collection.find_one(group) or {}
        self._cached[group] = doc

    def get(self, group, field):
        if group not in self._cached:
            self._load_doc(group)
        return self._cached[group].get(field)

    def set(self, group, field, value):
        self._changed[group][field] = value

    def commit(self):
        collection = self.collection
        for group in self._changed:
            doc = self._changed[group]
            if not doc:
                continue
            collection.update({
                '_id': group,
            }, {
                '$set': doc,
            }, upsert=True)
