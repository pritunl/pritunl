from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import logger

import importlib
import os
import threading

module_classes = []

for module_name in os.listdir(os.path.dirname(__file__)):
    if module_name in (
                '__init__.py',
                'group_base.py',
                'group_mongo.py',
                'group_file.py',
                'group_local.py',
            ) or module_name[-3:] != '.py':
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
        self._loaded = False
        self._init_modules()

    @cached_static_property
    def collection(cls):
        from pritunl import mongo
        return mongo.get_collection('system')

    @cached_property
    def groups(self):
        groups = set()

        for cls in module_classes:
            groups.add(cls.group)

        return groups

    def on_msg(self, msg):
        docs = msg['message']

        for doc in docs:
            group = getattr(self, doc['_id'])
            for field, val in doc.items():
                if field == '_id':
                    continue
                setattr(group, field, val)

    def commit(self, all_fields=False):
        from pritunl.messenger import Messenger
        from pritunl import mongo
        from pritunl import transaction

        docs = []
        has_docs = False
        messenger = Messenger()
        transaction = transaction.Transaction()
        collection = transaction.collection(
            self.collection.name_str)

        for group in self.groups:
            group_cls = getattr(self, group)
            if group_cls.type != GROUP_MONGO:
                continue

            doc = group_cls.get_commit_doc(all_fields)

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
        for cls in module_classes:
            if cls.type != GROUP_MONGO:
                continue
            setattr(self, cls.group, cls())

        for doc in self.collection.find():
            group_name = doc.pop('_id')
            if group_name not in self.groups:
                continue

            group = getattr(self, group_name)
            for field, val in doc.items():
                setattr(group, field, val)
        self._loaded = True

    def _init_modules(self):
        for cls in module_classes:
            if cls.type == GROUP_MONGO:
                continue
            group_cls = cls()
            if group_cls.type == GROUP_FILE:
                group_cls.load()
            setattr(self, cls.group, group_cls)

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

        self.load()

        self.commit(all_fields=True)
        listener.add_listener('setting', self.on_msg)

        self._start_check()

settings = Settings()
