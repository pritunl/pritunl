from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import importlib
import os
import threading

module_classes = []

for module_name in os.listdir(os.path.dirname(__file__)):
    if module_name == '__init__.py' or \
            module_name == 'group.py' or \
            module_name[-3:] != '.py':
        continue

    module_name = module_name[:-3]
    cls_name = 'Settings' + ''.join([x.capitalize()
        for x in module_name.split('_')])
    module = __import__('pritunl.settings.' + module_name,
        fromlist=(cls_name,))
    cls = getattr(module, cls_name)
    module_classes.append(cls)

class Settings(object):
    def __init__(self):
        self._running = False

    @cached_static_property
    def collection(cls):
        import pritunl.mongo as mongo
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
        from pritunl.mongo.transaction import MongoTransaction
        from pritunl.messenger import Messenger

        docs = []
        has_docs = False
        messenger = Messenger()
        transaction = MongoTransaction()
        collection = transaction.collection(
            self.collection.name_str)

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

    def _init_modules(self):
        for cls in module_classes:
            setattr(self, cls.group, cls())

    def _check(self):
        try:
            self.load()
        except:
            logger.exception('Auto settings check failed')
        self._start_check()

    def _start_check(self):
        thread = threading.Timer(self.app.settings_check_interval,
            self._check)
        thread.daemon = True
        thread.start()

    def start(self):
        import pritunl.listener as listener

        if self._running:
            return
        self._running = True

        self._init_modules()
        self.load()

        self.commit(all_fields=True)
        listener.add_listener('setting', self.on_msg)

        self._start_check()

settings = Settings()
