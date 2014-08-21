from constants import *
from pritunl import app_server
from cache import cache_db
from cache_trie import CacheTrie
from event import Event
from log_entry import LogEntry
from user import User
from mongo_object import MongoObject
import mongo
import uuid
import os
import subprocess
import utils
import logging
import threading
import random
import json

logger = logging.getLogger(APP_NAME)

class Organization(MongoObject):
    fields = {
        'name',
        'type',
        'ca_private_key',
        'ca_certificate',
    }

    def __init__(self, name=None, type=None, **kwargs):
        MongoObject.__init__(self, **kwargs)

        if name is not None:
            self.name = name
        if type is not None:
            self.type = type

    def __getattr__(self, name):
        if name == 'otp_auth':
            value = self._get_otp_auth()
            self.otp_auth = value
            return value
        elif name == 'user_count':
            value = self._get_user_count()
            self.user_count = value
            return value
        elif name == 'server_user_count':
            value = self._get_user_count(type=CERT_SERVER)
            self.server_user_count = value
            return value
        elif name == 'user_pool_count':
            value = self._get_user_count(type=CERT_CLIENT_POOL)
            self.user_pool_count = value
            return value
        elif name == 'server_user_pool_count':
            value = self._get_user_count(type=CERT_SERVER_POOL)
            self.server_user_pool_count = value
            return value
        elif name == 'page_total':
            # TODO
            return 0
        return MongoObject.__getattr__(self, name)

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_count': self.user_count,
        }

    @staticmethod
    def get_collection():
        return mongo.get_collection('organizations')

    def initialize(self):
        ca_user = User(org=self, type=CERT_CA)
        ca_user.initialize()
        self.ca_private_key = ca_user.private_key
        self.ca_certificate = ca_user.certificate

    def get_user(self, id):
        return User.get_user(org=self, id=id)

    def find_user(self, name=None, type=None):
        return User.find_user(org=self, name=name, type=type)

    def _get_otp_auth(self):
        from server import Server
        return bool(Server.get_collection().find_one({
            'organizations': self.id,
            'otp_auth': True,
        }))

    def _get_user_count(self, type=CERT_CLIENT):
        return User.get_collection().find({
            'org_id': self.id,
            'type': type,
        }).count()

    def iter_users(self, page=None, prefix=None, prefix_limit=None):
        spec = {
            'org_id': self.id,
            'type': CERT_CLIENT,
        }
        for doc in User.get_collection().find(spec).sort('name'):
            yield User(self, doc=doc)

    def create_user_key_link(self, user_id):
        key_id = uuid.uuid4().hex
        key_id_key = 'key_token-%s' % key_id

        view_id = None
        uri_id = None
        for i in xrange(2):
            for i in xrange(2048):
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
        if app_server.inline_certs:
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
        from server import Server
        server = Server.get_server(id=server_id)
        if server and self.id in server.organizations:
            return server

    def iter_servers(self):
        from server import Server
        for doc in Server.get_collection().find({'organizations': self.id}):
            yield Server(doc=doc)

    def new_user(self, **kwargs):
        user = User(org=self, **kwargs)
        user.initialize()
        return user

    def remove(self):
        for server in self.iter_servers():
            if server.status:
                server.stop()
            server.remove_org(self.id)
            server.commit()
        MongoObject.remove(self)
        User.get_collection().remove({'org_id': self.id})

    @classmethod
    def new_org(cls, **kwargs):
        org = cls(**kwargs)
        org.initialize()
        return org

    @classmethod
    def get_org(cls, id):
        return cls(id=id)

    @classmethod
    def get_org_count(cls, type=ORG_DEFAULT):
        return cls.get_collection().find({'type': type}).count()

    @classmethod
    def iter_orgs(cls, type=ORG_DEFAULT):
        for doc in cls.get_collection().find({'type': type}).sort('name'):
            yield cls(doc=doc)
