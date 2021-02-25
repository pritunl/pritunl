from pritunl.settings.app import SettingsApp
from pritunl.settings.conf import SettingsConf
from pritunl.settings.local import SettingsLocal
from pritunl.settings.mongo import SettingsMongo
from pritunl.settings.user import SettingsUser
from pritunl.settings.vpn import SettingsVpn

from pritunl.constants import *
from pritunl.helpers import *

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
        return mongo.get_collection('settings')

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
            for field, val in list(doc.items()):
                if field == '_id':
                    continue
                setattr(group, field, val)

    def commit(self, init=False):
        from pritunl import messenger
        from pritunl import transaction

        docs = []
        has_docs = False
        tran = transaction.Transaction()
        collection = tran.collection(self.collection.name_str)

        for group in self.groups:
            group_cls = getattr(self, group)
            if group_cls.type != GROUP_MONGO:
                continue

            doc = group_cls.get_commit_doc(init)
            if doc:
                has_docs = True
                collection.bulk().find({
                    '_id': doc['_id'],
                }).upsert().update({
                    '$set': doc,
                })

            unset_doc = group_cls.get_commit_unset_doc()
            if unset_doc:
                has_docs = True
                doc_id = unset_doc.pop('_id')
                collection.bulk().find({
                    '_id': doc_id,
                }).upsert().update({
                    '$unset': unset_doc,
                })

                doc = doc or {'_id': doc_id}
                for key in unset_doc:
                    doc[key] = getattr(group_cls, key)

            if doc:
                docs.append(doc)

        messenger.publish('setting', docs, transaction=tran)

        if not has_docs:
            return

        collection.bulk_execute()
        tran.commit()

    def _load_mongo(self):
        for cls in module_classes:
            if cls.type != GROUP_MONGO:
                continue
            setattr(self, cls.group, cls())

        self.reload_mongo()

        self._loaded = True

    def reload_mongo(self):
        for doc in self.collection.find():
            group_name = doc.pop('_id')
            if group_name not in self.groups:
                continue

            group = getattr(self, group_name)

            data = {}
            data.update(group.fields)
            data.update(doc)

            group.__dict__.update(data)

    def _init_modules(self):
        for cls in module_classes:
            if cls.type == GROUP_MONGO:
                continue
            group_cls = cls()
            if group_cls.type == GROUP_FILE:
                group_cls.load()
            setattr(self, cls.group, group_cls)

    def init(self):
        self._load_mongo()
        self.commit(True)
