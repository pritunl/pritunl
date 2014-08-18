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

    def _load_doc(self, id):
        doc = self.get_collection().find_one(id) or {}
        self._cached[id] = doc

    def get(self, name):
        id, field = name.split('.')
        if id not in self._cached:
            self._load_doc(id)
        return self._cached[id].get(field)

    def set(self, name, value):
        id, field = name.split('.')
        self._changed[id][field] = value

    def commit(self):
        collection = self.get_collection()
        for id in self._changed:
            doc = self._changed[id]
            if not doc:
                continue
            collection.update({
                '_id': id,
            }, {
                '$set': doc,
            }, upsert=True)
