from constants import *
from exceptions import *
import mongo
import collections

class SystemConf():
    def __init__(self):
        self._cached = {}
        self._changed = collections.defaultdict(lambda: {})

    @staticmethod
    def get_collection():
        return mongo.get_collection('system')

    def _load_doc(self, group):
        doc = self.get_collection().find_one(group) or {}
        self._cached[group] = doc

    def get(self, group, field):
        if group not in self._cached:
            self._load_doc(group)
        return self._cached[group].get(field)

    def set(self, group, field, value):
        self._changed[group][field] = value

    def commit(self):
        collection = self.get_collection()
        for group in self._changed:
            doc = self._changed[group]
            if not doc:
                continue
            collection.update({
                '_id': group,
            }, {
                '$set': doc,
            }, upsert=True)
