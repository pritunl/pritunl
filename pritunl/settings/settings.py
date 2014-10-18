from pritunl.settings.app import SettingsApp
from pritunl.settings.conf import SettingsConf
from pritunl.settings.local import SettingsLocal
from pritunl.settings.mongo import SettingsMongo
from pritunl.settings.user import SettingsUser
from pritunl.settings.vpn import SettingsVpn

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

import importlib
import os
import threading
import sys

module_classes = (
    SettingsApp,
    SettingsConf,
    SettingsLocal,
    SettingsMongo,
    SettingsUser,
    SettingsVpn,
)

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
        from pritunl import messenger
        from pritunl import mongo
        from pritunl import transaction

        docs = []
        has_docs = False
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

    def load_mongo(self):
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

    def init(self):
        self.load_mongo()
        self.commit(all_fields=True)
