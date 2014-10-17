from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import app
from pritunl import logger
from pritunl import mongo
from pritunl import queue
from pritunl import pooler
from pritunl import user
from pritunl import utils

import uuid
import logging
import random
import json
import math
import pymongo
import threading

class Organization(mongo.MongoObject):
    fields = {
        'name',
        'type',
        'ca_private_key',
        'ca_certificate',
    }
    fields_default = {
        'type': ORG_DEFAULT,
    }
    fields_required = {
        'type',
        'ca_private_key',
        'ca_certificate',
    }

    def __init__(self, name=None, type=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)
        self.last_search_count = None
        self.processes = []
        self.queue_com = queue.QueueCom()

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
        return bool(self.server_collection.find({
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
        return math.floor(max(0, float(self.user_count - 1)) /
            settings.user.page_count)

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('organizations')

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

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

        logger.debug('Init ca_user', 'organization',
            org_id=self.id,
            user_id=ca_user.id,
        )

        self.ca_private_key = ca_user.private_key
        self.ca_certificate = ca_user.certificate

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
            logger.debug('Fill new org pool', 'organization',
                org_id=self.id,
            )

            thread = threading.Thread(
                target=pooler.fill,
                args=(
                    'new_user',
                    self,
                ),
            )
            thread.daemon = True
            thread.start()

    def get_user(self, id):
        return user.get_user(org=self, id=id)

    def find_user(self, name=None, type=None, resource_id=None):
        return user.find_user(org=self, name=name, type=type,
            resource_id=resource_id)

    def _get_user_count(self, type=CERT_CLIENT):
        return user.User.collection.find({
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
        limit = None
        skip = None
        page_count = settings.user.page_count

        if fields:
            fields = {key: True for key in fields}

        if search is not None:
            spec['name'] = {'$regex': '.*%s.*' % search}
            limit = search_limit or page_count
        elif page is not None:
            limit = page_count
            skip = page * page_count if page else 0

        sort = [
            ('type', pymongo.ASCENDING),
            ('name', pymongo.ASCENDING),
        ]

        cursor = user.User.collection.find(spec, fields).sort(sort)

        if skip is not None:
            cursor = cursor.skip(page * page_count if page else 0)
        if limit is not None:
            cursor = cursor.limit(limit)

        if search:
            self.last_search_count = cursor.count()

        for doc in cursor:
            yield user.User(self, doc=doc)

    def create_user_key_link(self, user_id):
        success = False
        for _ in xrange(256):
            key_id = uuid.uuid4().hex
            short_id = ''.join(random.sample(
                    SHORT_URL_CHARS, settings.app.short_url_length))

            try:
                self.key_link_collection.update({
                    'org_id': self.id,
                    'user_id': user_id,
                }, {'$set': {
                    'key_id': key_id,
                    'short_id': short_id,
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
            'view_url': '/k/%s' % short_id,
            'uri_url': '/ku/%s' % short_id,
        }

    def get_server(self, server_id):
        from pritunl import server
        svr = server.get_server(id=server_id)
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
            yield server.Server(doc=doc)

    def new_user(self, type=CERT_CLIENT, block=True, **kwargs):
        # First attempt to get user from pool then attempt to get
        # unfinished queued user in pool then queue a new user init
        if type in (CERT_SERVER, CERT_CLIENT):
            usr = user.reserve_pooled_user(org=self, type=type, **kwargs)

            if not usr:
                usr = queue.reserve('queued_user', org=self, type=type,
                    block=block, **kwargs)

                if usr:
                    logger.debug('Reserved queued user', 'organization',
                        org_id=self.id,
                        user_id=usr.id,
                    )
            else:
                logger.debug('Reserved pooled user', 'organization',
                    org_id=self.id,
                    user_id=usr.id,
                )

            if usr:
                user.new_pooled_user(org=self, type=type)
                return usr

        usr = user.User(org=self, type=type, **kwargs)
        usr.queue_initialize(block=block,
            priority=HIGH if type in (CERT_SERVER, CERT_CLIENT) else None)

        logger.debug('Queued user init', 'organization',
            org_id=self.id,
            user_id=usr.id,
        )

        return usr

    def remove(self):
        logger.debug('Remove org', 'organization',
            org_id=self.id,
        )

        for server in self.iter_servers():
            if server.status:
                server.stop()
            server.remove_org(self)
            server.commit()
        mongo.MongoObject.remove(self)
        user.User.collection.remove({
            'org_id': self.id,
        })

def new_pooled_org():
    thread = threading.Thread(target=new_org, kwargs={
        'type': ORG_POOL,
        'block': False,
    })
    thread.daemon = True
    thread.start()

    logger.debug('Queued pooled org', 'organization')

def reserve_pooled_org(name=None, type=ORG_DEFAULT):
    doc = {}

    if name is not None:
        doc['name'] = name
    if type is not None:
        doc['type'] = type

    doc = Organization.collection.find_and_modify({
        'type': ORG_POOL,
    }, {
        '$set': doc,
    })

    if doc:
        return Organization(doc=doc)

def new_org(type=ORG_DEFAULT, block=True, **kwargs):
    if type == ORG_DEFAULT:
        org = reserve_pooled_org(type=type, **kwargs)

        if not org:
            org = queue.reserve('queued_org', block=block, type=type,
                **kwargs)

            if org:
                logger.debug('Reserved queued org', 'organization',
                    org_id=org.id,
                )
        else:
            logger.debug('Reserved pooled org', 'organization',
                org_id=org.id,
            )

        if org:
            new_pooled_org()
            return org

        org = Organization(type=type, **kwargs)
        org.initialize()
        org.commit()

        logger.debug('Org init', 'organization',
            org_id=org.id,
        )

        return org
    else:
        org = Organization(type=type, **kwargs)
        org.queue_initialize(block=block)

        logger.debug('Queue org init', 'organization',
            org_id=org.id,
        )

        return org

def get_org(id):
    return Organization(id=id)

def iter_orgs(type=ORG_DEFAULT):
    spec = {}
    if type is not None:
        spec['type'] = type

    for doc in Organization.collection.find(spec).sort('name'):
        yield Organization(doc=doc)

def get_user_count_multi(org_ids=None, type=CERT_CLIENT):
    spec = {
        'type': type,
    }
    if org_ids is not None:
        spec['org_id'] = {'$in': org_ids}
    return user.User.collection.find(spec).count()
