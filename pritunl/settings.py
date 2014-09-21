from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings_test import SettingsTest
from pritunl.messenger import Messenger
from pritunl.mongo_transaction import MongoTransaction
import pritunl.mongo as mongo
import pritunl.listener as listener

class Settings(object):
    def __init__(self):
        self._listening = False

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('system')

    def on_msg(self, msg):
        docs = msg['message']

        for doc in docs:
            group = getattr(self, doc['_id'])
            for field, val in doc.items():
                if field == '_id':
                    continue
                setattr(group, field, val)

    def commit(self, all_fields=False):
        docs = []
        has_docs = False
        messenger = Messenger()
        transaction = MongoTransaction()
        collection = transaction.collection(
            self.collection.collection_name)

        for group in dir(self):
            if group[0] == '_' or group in SETTINGS_RESERVED:
                continue
            doc = getattr(self, group).get_commit_doc(all_fields)

            if doc:
                has_docs = True
                collection.bulk().find({
                    '_id': doc['_id'],
                }).upsert().update({
                    '$set': doc,
                })
                docs.append(doc)

        messenger.publish('setting', docs, transaction=transaction)

        if not has_docs:
            return

        collection.bulk_execute()
        transaction.commit()

    def load(self):
        groups = set(dir(self)) - SETTINGS_RESERVED
        for doc in self.collection.find():
            group_name = doc.pop('_id')
            if group_name not in groups:
                continue

            group = getattr(self, group_name)
            for field, val in doc.items():
                setattr(group, field, val)

    def start(self):
        self.load()
        if not self._listening:
            self.commit(all_fields=True)
            self._listening = True
            listener.add_listener('setting', self.on_msg)

settings = Settings()
