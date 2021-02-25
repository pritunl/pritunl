from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import queue
from pritunl import pooler
from pritunl import user
from pritunl import utils

import uuid
import math
import pymongo
import threading
import hashlib
import re

class Organization(mongo.MongoObject):
    fields = {
        'name',
        'type',
        'auth_api',
        'auth_token',
        'auth_secret',
        'ca_private_key',
        'ca_certificate',
    }
    fields_default = {
        'type': ORG_DEFAULT,
        'auth_api': False,
    }
    fields_required = {
        'type',
        'ca_private_key',
        'ca_certificate',
    }

    def __init__(self, name=None, auth_api=None, type=None, **kwargs):
        mongo.MongoObject.__init__(self)
        self.last_search_count = None
        self.processes = []
        self.queue_com = queue.QueueCom()

        if name is not None:
            self.name = name
        if auth_api is not None:
            self.auth_api = auth_api
        if type is not None:
            self.type = type

    @property
    def journal_data(self):
        return {
            'organization_id': self.id,
            'organization_name': self.name,
        }

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'auth_api': self.auth_api,
            'auth_token': self.auth_token,
            'auth_secret': self.auth_secret,
            'user_count': self.user_count,
        }

    @property
    def otp_auth(self):
        return bool(self.server_collection.find({
            'organizations': self.id,
            'otp_auth': True,
        }, {
            '_id': True,
        }).limit(1).count())

    @cached_property
    def user_count(self):
        return self._get_user_count(type=CERT_CLIENT)

    @cached_property
    def server_user_count(self):
        return self._get_user_count(type=CERT_SERVER)

    @property
    def page_total(self):
        return int(math.floor(max(0, float(self.user_count - 1)) /
            settings.user.page_count))

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('organizations')

    @cached_static_property
    def clients_collection(cls):
        return mongo.get_collection('clients')

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def nonces_collection(cls):
        return mongo.get_collection('auth_nonces')

    @cached_static_property
    def key_link_collection(cls):
        return mongo.get_collection('users_key_link')

    def initialize(self, queue_user_init=True):
        ca_user = user.User(org=self, type=CERT_CA)

        if queue_user_init:
            ca_user.queue_initialize(block=True,
                priority=HIGH if self.type == ORG_DEFAULT else None)
        else:
            ca_user.initialize()
            ca_user.commit()

        self.ca_private_key = ca_user.private_key
        self.ca_certificate = ca_user.certificate

    def generate_auth_token(self):
        self.auth_token = utils.generate_secret()

    def generate_auth_secret(self):
        self.auth_secret = utils.generate_secret()

    def queue_initialize(self, block, priority=LOW):
        if self.type != ORG_POOL:
            raise TypeError('Only pool orgs can be queued')

        queue.start('init_org_pooled', block=block,
            org_doc=self.export(), priority=priority)

        if block:
            self.load()

    def commit(self, *args, **kwargs):
        exists = self.exists
        mongo.MongoObject.commit(self, *args, **kwargs)

        if not exists:
            thread = threading.Thread(
                target=pooler.fill,
                args=(
                    'new_user',
                    self,
                ),
            )
            thread.daemon = True
            thread.start()

    def get_user(self, id, fields=None):
        return user.get_user(org=self, id=id, fields=fields)

    def find_user(self, name=None, type=None, resource_id=None):
        return user.find_user(org=self, name=name, type=type,
            resource_id=resource_id)

    def _get_user_count(self, type=CERT_CLIENT):
        return user.User.collection.find({
            'type': type,
            'org_id': self.id,
        }, {
            '_id': True,
        }).count()

    def iter_users(self, page=None, search=None, search_limit=None,
            fields=None, include_pool=False):
        spec = {
            'org_id': self.id,
            'type': CERT_CLIENT,
        }
        searched = False
        type_search = False
        limit = None
        skip = None
        page_count = settings.user.page_count

        if fields:
            fields = {key: True for key in fields}

        if search is not None:
            searched = True

            n = search.find('id:')
            if n != -1:
                user_id = search[n + 3:].split(None, 1)
                user_id = user_id[0] if user_id else ''
                if user_id:
                    type_search = True
                    spec['_id'] = utils.ObjectId(user_id)
                search = search[:n] + search[n + 3 + len(user_id):].strip()

            n = search.find('type:')
            if n != -1:
                user_type = search[n + 5:].split(None, 1)
                user_type = user_type[0] if user_type else ''
                if user_type:
                    type_search = True
                    spec['type'] = user_type
                search = search[:n] + search[n + 5 + len(user_type):].strip()

            n = search.find('group:')
            if n != -1:
                user_group = search[n + 6:].split(None, 1)
                user_group = user_group[0] if user_group else ''
                if user_group:
                    spec['groups'] = user_group
                search = search[:n] + search[n + 6 + len(user_group):].strip()

            n = search.find('email:')
            if n != -1:
                email = search[n + 6:].split(None, 1)
                email = email[0] if email else ''
                if email:
                    spec['email'] = {
                        '$regex': '.*%s.*' % re.escape(email),
                        '$options': 'i',
                    }
                search = search[:n] + search[n + 6 + len(email):].strip()

            n = search.find('status:')
            if n != -1:
                status = search[n + 7:].split(None, 1)
                status = status[0] if status else ''
                search = search[:n] + search[n + 7 + len(status):].strip()

                if status not in (ONLINE, OFFLINE):
                    return

                user_ids = self.clients_collection.find(None, {
                    '_id': True,
                    'user_id': True,
                }).distinct('user_id')

                if status == ONLINE:
                    spec['_id'] = {'$in': user_ids}
                else:
                    spec['_id'] = {'$nin': user_ids}

            spec['name'] = {
                '$regex': '.*%s.*' % re.escape(search).strip(),
                '$options': 'i',
            }

            limit = search_limit or page_count
        elif page is not None:
            limit = page_count
            skip = page * page_count if page else 0

        cursor = user.User.collection.find(spec, fields).sort(
            'name', pymongo.ASCENDING)

        if skip is not None:
            cursor = cursor.skip(page * page_count if page else 0)
        if limit is not None:
            cursor = cursor.limit(limit + 1)

        if searched:
            self.last_search_count = cursor.count()

        if limit is None:
            for doc in cursor:
                yield user.User(self, doc=doc, fields=fields)
        else:
            count = 0
            for doc in cursor:
                count += 1
                if count > limit:
                    return
                yield user.User(self, doc=doc, fields=fields)

        if type_search:
            return

        if include_pool:
            spec['type'] = {'$in': [CERT_SERVER, CERT_CLIENT_POOL,
                CERT_SERVER_POOL]}
        else:
            spec['type'] = CERT_SERVER

        cursor = user.User.collection.find(spec, fields).sort(
            'name', pymongo.ASCENDING)

        for doc in cursor:
            yield user.User(self, doc=doc, fields=fields)

    def create_user_key_link(self, user_id, one_time=False):
        success = False
        for _ in range(256):
            key_id = utils.rand_str(32)

            if one_time:
                short_id = utils.rand_str(settings.app.long_url_length)
            else:
                short_id = utils.rand_str_ne(settings.app.short_url_length)

            try:
                self.key_link_collection.update({
                    'org_id': self.id,
                    'user_id': user_id,
                }, {'$set': {
                    'key_id': key_id,
                    'short_id': short_id,
                    'one_time': one_time,
                    'timestamp': utils.now(),
                }}, upsert=True)
            except pymongo.errors.DuplicateKeyError:
                continue

            success = True
            break

        if not success:
            raise KeyLinkError('Failed to generate random key short id')

        return {
            'id': key_id,
            'key_url': '/key/%s.tar' % key_id,
            'key_zip_url': '/key/%s.zip' % key_id,
            'key_onc_url': '/key_onc/%s.onc' % key_id,
            'view_url': '/k/%s' % short_id,
            'uri_url': '/ku/%s' % short_id,
        }

    def get_by_id(self, server_id):
        from pritunl import server
        svr = server.get_by_id(server_id)
        if svr and self.id in svr.organizations:
            return svr

    def iter_servers(self, fields=None):
        from pritunl import server

        spec = {
            'organizations': self.id,
        }
        if fields:
            fields = {key: True for key in fields}

        for doc in server.Server.collection.find(spec, fields):
            yield server.Server(doc=doc, fields=fields)

    def new_user(self, type=CERT_CLIENT, block=True, pool=True, **kwargs):
        # First attempt to get user from pool then attempt to get
        # unfinished queued user in pool then queue a new user init
        if type in (CERT_SERVER, CERT_CLIENT) and pool:
            usr = user.reserve_pooled_user(org=self, type=type, **kwargs)

            if not usr:
                usr = queue.reserve('queued_user', org=self, type=type,
                    block=block, **kwargs)

            if usr:
                user.new_pooled_user(org=self, type=type)
                return usr

        usr = user.User(org=self, type=type, **kwargs)
        usr.queue_initialize(block=block,
            priority=HIGH if type in (CERT_SERVER, CERT_CLIENT) else None)

        return usr

    def remove(self):
        user_collection = mongo.get_collection('users')
        user_audit_collection = mongo.get_collection('users_audit')
        user_net_link_collection = mongo.get_collection('users_net_link')
        server_collection = mongo.get_collection('servers')

        user_audit_collection.remove({
            'org_id': self.id,
        })

        user_net_link_collection.remove({
            'org_id': self.id,
        })

        server_ids = []

        for server in self.iter_servers():
            server_ids.append(server.id)
            if server.status == ONLINE:
                server.stop()

        server_collection.update({
            'organizations': self.id,
        }, {'$pull': {
            'organizations': self.id,
        }})

        mongo.MongoObject.remove(self)
        user_collection.remove({
            'org_id': self.id,
        })

        return server_ids
