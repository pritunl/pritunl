from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.cache import cache_db
from pritunl.user import User
from pritunl.pooler_user import PoolerUser
from pritunl.mongo_object import MongoObject
from pritunl.queue_init_org_pooled import QueueInitOrgPooled
from pritunl import app_server
import pritunl.mongo as mongo
import uuid
import logging
import random
import json
import math
import pymongo
import threading

logger = logging.getLogger(APP_NAME)

class Organization(MongoObject):
    fields = {
        'name',
        'type',
        'ca_private_key',
        'ca_certificate',
    }
    fields_default = {
        'type': ORG_DEFAULT,
    }

    def __init__(self, name=None, type=None, **kwargs):
        MongoObject.__init__(self, **kwargs)
        self.last_search_count = None

        if name is not None:
            self.name = name
        if type is not None:
            self.type = type

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_count': self.user_count,
        }

    @property
    def otp_auth(self):
        from pritunl.server import Server
        return bool(Server.collection.find({
            'organizations': self.id,
            'otp_auth': True,
        }, {
            '_id': True,
        }).limit(1).count())

    @property
    def user_count(self):
        return self._get_user_count(type=CERT_CLIENT)

    @property
    def server_user_count(self):
        return self._get_user_count(type=CERT_SERVER)

    @property
    def page_total(self):
        return math.floor(max(0, float(self.user_count - 1)) / USER_PAGE_COUNT)

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('organizations')

    def initialize(self, queue_user_init=True):
        ca_user = User(org=self, type=CERT_CA)

        if queue_user_init:
            ca_user.queue_initialize(block=True)
        else:
            ca_user.initialize()
            ca_user.commit()

        self.ca_private_key = ca_user.private_key
        self.ca_certificate = ca_user.certificate

    def queue_initialize(self, block):
        if self.type != ORG_POOL:
            raise TypeError('Only pool orgs can be queued')
        queue = QueueInitOrgPooled(org_doc=self.export())
        queue.start(block=block)

    def commit(self, *args, **kwargs):
        exists = self.exists
        MongoObject.commit(self, *args, **kwargs)

        if not exists:
            thread = threading.Thread(target=PoolerUser.fill_new_org_pool,
                kwargs={
                    'org': self,
                })
            thread.daemon = True
            thread.start()

    def get_user(self, id):
        return User.get_user(org=self, id=id)

    def find_user(self, name=None, type=None):
        return User.find_user(org=self, name=name, type=type)

    def _get_user_count(self, type=CERT_CLIENT):
        return User.collection.find({
            'org_id': self.id,
            'type': type,
        }, {
            '_id': True,
        }).count()

    def iter_users(self, page=None, search=None, search_limit=None,
            fields=None):
        spec = {
            'org_id': self.id,
            'type': {'$in': [CERT_CLIENT, CERT_SERVER]},
        }
        if fields:
            fields = {key: True for key in fields}

        if search:
            spec['name'] = {'$regex': '.*%s.*' % search}
            limit = search_limit or USER_PAGE_COUNT
        else:
            limit = USER_PAGE_COUNT

        sort = [
            ('type', pymongo.ASCENDING),
            ('name', pymongo.ASCENDING),
        ]
        skip = page * USER_PAGE_COUNT if page else 0

        cursor = User.collection.find(spec, fields).sort(
            sort).skip(skip).limit(limit)

        if search:
            self.last_search_count = cursor.count()

        for doc in cursor:
            yield User(self, doc=doc)

    def create_user_key_link(self, user_id):
        key_id = uuid.uuid4().hex
        key_id_key = 'key_token-%s' % key_id

        view_id = None
        uri_id = None
        for _ in xrange(2):
            for _ in xrange(2048):
                temp_id = ''.join(random.sample(
                    SHORT_URL_CHARS, SHORT_URL_LEN))
                if not view_id:
                    if not cache_db.exists('view_token-%s' % temp_id):
                        view_id = temp_id
                        break
                else:
                    if not cache_db.exists('uri_token-%s' % temp_id):
                        uri_id = temp_id
                        break
            if not view_id and not uri_id:
                raise KeyLinkError('Failed to generate random id')
        view_id_key = 'view_token-%s' % view_id
        uri_id_key = 'uri_token-%s' % uri_id

        cache_db.expire(key_id_key, KEY_LINK_TIMEOUT)
        cache_db.dict_set(key_id_key, 'org_id', self.id)
        cache_db.dict_set(key_id_key, 'user_id', user_id)
        cache_db.dict_set(key_id_key, 'view_id', view_id)
        cache_db.dict_set(key_id_key, 'uri_id', uri_id)

        conf_urls = []
        for server in self.iter_servers():
            conf_id = uuid.uuid4().hex
            conf_id_key = 'conf_token-%s' % conf_id

            cache_db.expire(conf_id_key, KEY_LINK_TIMEOUT)
            cache_db.dict_set(conf_id_key, 'org_id', self.id)
            cache_db.dict_set(conf_id_key, 'user_id', user_id)
            cache_db.dict_set(conf_id_key, 'server_id', server.id)

            conf_urls.append({
                'id': conf_id,
                'server_name': server.name,
                'url': '/key/%s.ovpn' % conf_id,
            })

        cache_db.expire(view_id_key, KEY_LINK_TIMEOUT)
        cache_db.dict_set(view_id_key, 'org_id', self.id)
        cache_db.dict_set(view_id_key, 'user_id', user_id)
        cache_db.dict_set(view_id_key, 'key_id', key_id)
        cache_db.dict_set(view_id_key, 'uri_id', uri_id)
        cache_db.dict_set(view_id_key,
            'conf_urls', json.dumps(conf_urls))

        cache_db.expire(uri_id_key, KEY_LINK_TIMEOUT)
        cache_db.dict_set(uri_id_key, 'org_id', self.id)
        cache_db.dict_set(uri_id_key, 'user_id', user_id)

        return {
            'id': key_id,
            'key_url': '/key/%s.tar' % key_id,
            'view_url': '/k/%s' % view_id,
            'uri_url': '/ku/%s' % uri_id,
        }

    def get_server(self, server_id):
        from pritunl.server import Server
        server = Server.get_server(id=server_id)
        if server and self.id in server.organizations:
            return server

    def iter_servers(self, fields=None):
        from pritunl.server import Server
        spec = {
            'organizations': self.id,
        }
        if fields:
            fields = {key: True for key in fields}
        for doc in Server.collection.find(spec, fields):
            yield Server(doc=doc)

    def new_user(self, type=CERT_CLIENT, block=True, **kwargs):
        # First attempt to get user from pool then attempt to get
        # unfinished queued user in pool then queue a new user init
        if type in (CERT_SERVER, CERT_CLIENT):
            user = User.reserve_pooled_user(org=self, type=type, **kwargs)

            if not user:
                user = User.reserve_queued_user(org=self, type=type,
                    block=block, **kwargs)

            if user:
                User.new_pooled_user(org=self, type=type)
                return user

        user = User(org=self, type=type, **kwargs)
        user.queue_initialize(block=block)
        return user

    def remove(self):
        for server in self.iter_servers():
            if server.status:
                server.stop()
            server.remove_org(self)
            server.commit()
        MongoObject.remove(self)
        User.collection.remove({
            'org_id': self.id,
        })

    @classmethod
    def new_pooled_org(cls):
        thread = threading.Thread(target=cls.new_org, kwargs={
            'type': ORG_POOL,
            'block': False,
        })
        thread.daemon = True
        thread.start()

    @classmethod
    def reserve_pooled_org(cls, name=None, type=ORG_DEFAULT):
        doc = {}

        if name is not None:
            doc['name'] = name
        if type is not None:
            doc['type'] = type

        doc = cls.collection.find_and_modify({
            'type': ORG_POOL,
        }, {
            '$set': doc,
        })

        if doc:
            return cls(doc=doc)

    @staticmethod
    def reserve_queued_org(block, **kwargs):
        return QueueInitOrgPooled.reserve_queued_org(
            block=block, **kwargs)

    @classmethod
    def new_org(cls, type=ORG_DEFAULT, block=True, **kwargs):
        if type == ORG_DEFAULT:
            org = cls.reserve_pooled_org(type=type, **kwargs)

            if not org:
                org = cls.reserve_queued_org(type=type,
                    block=block, **kwargs)

            if org:
                cls.new_pooled_org()
                return org

            org = cls(type=type, **kwargs)
            org.initialize()
            org.commit()
            return org
        else:
            org = cls(type=type, **kwargs)
            org.queue_initialize(block=block)
            return org

    @classmethod
    def get_org(cls, id):
        return cls(id=id)

    @classmethod
    def iter_orgs(cls, type=ORG_DEFAULT):
        spec = {}
        if type is not None:
            spec['type'] = type

        for doc in cls.collection.find(spec).sort('name'):
            yield cls(doc=doc)

    @classmethod
    def get_user_count_multi(cls, org_ids=None, type=CERT_CLIENT):
        spec = {
            'type': type,
        }
        if org_ids is not None:
            spec['org_id'] = {'$in': org_ids}
        return User.collection.find(spec).count()
