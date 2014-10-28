from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import ipaddress

import bson
import pymongo

class ServerIpPool:
    def __init__(self, server):
        self.server = server

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers_ip_pool')

    @cached_static_property
    def users_collection(cls):
        return mongo.get_collection('users')

    def assign_ip_addr(self, org_id, user_id):
        network = self.server.network
        server_id = self.server.id

        response = self.collection.update({
            'network': network,
            'server_id': server_id,
            'user_id': {'$exists': False},
        }, {'$set': {
            'org_id': org_id,
            'user_id': user_id,
        }})
        if response['updatedExisting']:
            return

        ip_network = ipaddress.IPv4Network(network)
        ip_pool = ip_network.iterhosts()
        ip_pool.next()

        try:
            doc = self.collection.find({
                'network': network,
                'server_id': server_id,
            }).sort('_id', pymongo.DESCENDING)[0]
            if doc:
                last_addr = doc['_id']
                for remote_ip_addr in ip_pool:
                    if int(remote_ip_addr) == last_addr:
                        break
        except IndexError:
            pass

        for remote_ip_addr in ip_pool:
            try:
                self.collection.insert({
                    '_id': int(remote_ip_addr),
                    'network': network,
                    'server_id': server_id,
                    'org_id': org_id,
                    'user_id': user_id,
                    'address': '%s/%s' % (remote_ip_addr,
                        ip_network.prefixlen),
                })
                return
            except pymongo.errors.DuplicateKeyError:
                pass

        logger.warning('Failed to assign ip address ' +
            'to user, ip pool empty. %r' % {
                'org_id': org_id,
                'user_id': user_id,
            })

    def unassign_ip_addr(self, org_id, user_id):
        self.collection.update({
            'server_id': self.server.id,
            'network': self.server.network,
            'user_id': user_id,
        }, {'$unset': {
            'org_id': '',
            'user_id': '',
        }})

    def assign_ip_pool_org(self, org):
        network = self.server.network
        server_id = self.server.id
        org_id = org.id
        ip_pool_avial = True
        pool_end = False

        ip_network = ipaddress.IPv4Network(network)
        ip_pool = ip_network.iterhosts()
        ip_pool.next()

        try:
            doc = self.collection.find({
                'network': network,
                'server_id': server_id,
            }).sort('_id', pymongo.DESCENDING)[0]
            if doc:
                last_addr = doc['_id']
                for remote_ip_addr in ip_pool:
                    if int(remote_ip_addr) == last_addr:
                        break
        except IndexError:
            pass

        if mongo.has_bulk:
            bulk = self.collection.initialize_unordered_bulk_op()
            bulk_empty = True
        else:
            bulk = None
            bulk_empty = None

        for user in org.iter_users(include_pool=True):
            if ip_pool_avial:
                response = self.collection.update({
                    'network': network,
                    'server_id': server_id,
                    'user_id': {'$exists': False},
                }, {'$set': {
                    'org_id': org_id,
                    'user_id': user.id,
                }})
                if response['updatedExisting']:
                    continue
                ip_pool_avial = False

            try:
                remote_ip_addr = ip_pool.next()
            except StopIteration:
                pool_end = True
                break
            doc_id = int(remote_ip_addr)

            spec = {
                '_id': doc_id,
            }
            doc = {'$set': {
                '_id': doc_id,
                'network': network,
                'server_id': server_id,
                'org_id': org_id,
                'user_id': user.id,
                'address': '%s/%s' % (remote_ip_addr,
                    ip_network.prefixlen),
            }}

            if bulk:
                bulk.find(spec).upsert().update(doc)
                bulk_empty = False
            else:
                self.collection.update(spec, doc, upsert=True)

        if bulk and not bulk_empty:
            bulk.execute()

        if pool_end:
            logger.warning('Failed to assign ip addresses ' +
                'to org, ip pool empty. %r' % {
                    'org_id': org_id,
                    'user_id': user_id,
                })

    def assign_ip_pool(self, network):
        server_id = self.server.id
        pool_end = False

        ip_network = ipaddress.IPv4Network(network)
        ip_pool = ip_network.iterhosts()
        ip_pool.next()

        if mongo.has_bulk:
            bulk = self.collection.initialize_unordered_bulk_op()
            bulk_empty = True
        else:
            bulk = None
            bulk_empty = None

        for org in self.server.iter_orgs():
            org_id = org.id

            for user in org.iter_users():
                try:
                    remote_ip_addr = ip_pool.next()
                except StopIteration:
                    pool_end = True
                    break
                doc_id = int(remote_ip_addr)

                spec = {
                    '_id': doc_id,
                }
                doc = {'$set': {
                    '_id': doc_id,
                    'network': network,
                    'server_id': server_id,
                    'org_id': org_id,
                    'user_id': user.id,
                    'address': '%s/%s' % (remote_ip_addr,
                        ip_network.prefixlen),
                }}

                if bulk:
                    bulk.find(spec).upsert().update(doc)
                    bulk_empty = False
                else:
                    self.collection.update(spec, doc, upsert=True)

            if pool_end:
                break

        if bulk and not bulk_empty:
            bulk.execute()

    def sync_ip_pool(self):
        server_id = self.server.id

        if mongo.has_bulk:
            bulk = self.collection.initialize_unordered_bulk_op()
        else:
            bulk = None

        spec = {
            'server_id': server_id,
            'network': {'$ne': self.server.network},
        }
        if bulk:
            bulk.find(spec).remove()
        else:
            self.collection.remove(spec)

        dup_user_ips = self.collection.aggregate([
            {'$match': {
                'server_id': server_id,
                'user_id': {'$exists': True},
            }},
            {'$project': {
                'user_id': True,
            }},
            {'$group': {
                '_id': '$user_id',
                'ids': {'$addToSet': '$_id'},
                'count': {'$sum': 1},
            }},
            {'$match': {
                'count': {'$gt': 1},
            }},
        ])
        for dup_user_ip in dup_user_ips['result']:
            for doc_id in dup_user_ip['ids'][1:]:
                spec = {
                    '_id': doc_id,
                }
                doc = {'$unset': {
                    'org_id': '',
                    'user_id': '',
                }}

                if bulk:
                    bulk.find(spec).update(doc)
                else:
                    self.collection.update(spec, doc)

        user_ids = self.users_collection.find({
            'org_id': {'$in': self.server.organizations},
        }, {
            'user_id': True,
        }).distinct('_id')
        user_ids = set(user_ids)

        user_ip_ids = self.collection.find({
            'server_id': server_id,
        }, {
            'user_id': True,
        }).distinct('user_id')
        user_ip_ids = set(user_ip_ids)

        for user_id in user_ip_ids - user_ids:
            spec = {
                'server_id': server_id,
                'network': self.server.network,
                'user_id': user_id,
            }
            doc = {'$unset': {
                'org_id': '',
                'user_id': '',
            }}

            if bulk:
                bulk.find(spec).update(doc)
            else:
                self.collection.update(spec, doc)

        if bulk:
            bulk.execute()

        for user_id in user_ids - user_ip_ids:
            doc = self.users_collection.find_one(user_id, {
                'org_id': True,
            })
            if doc:
                self.assign_ip_addr(doc['org_id'], user_id)

    def get_ip_addr(self, org_id, user_id):
        doc = self.collection.find_one({
            'server_id': self.server.id,
            'network': self.server.network,
            'user_id': user_id,
        }, {
            'address': True,
        })

        if doc:
            return doc['address']

def multi_get_ip_addr(org_id, user_ids):
    spec = {
        'user_id': {'$in': user_ids},
    }
    project = {
        '_id': False,
        'user_id': True,
        'server_id': True,
        'address': True,
    }

    for doc in ServerIpPool.collection.find(spec, project):
        yield doc['user_id'], doc['server_id'], doc['address'].split('/')[0]
