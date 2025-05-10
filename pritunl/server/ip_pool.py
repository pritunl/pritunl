from pritunl.helpers import *
from pritunl import mongo
from pritunl import ipaddress
from pritunl import organization
from pritunl import logger
from pritunl import settings
from pritunl import utils

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

    def get_ip_pool(self, network, network_start):
        ip_pool = network.hosts()

        if network_start:
            network_start = ipaddress.IPv4Address(network_start)
            network_break = network_start - 1

            while True:
                try:
                    ip_addr = next(ip_pool)
                except StopIteration:
                    logger.error('Failed to find network start', 'server',
                        server_id=self.server.id,
                    )
                    return

                if ip_addr == network_break:
                    break
        else:
            next(ip_pool)

        return ip_pool

    def assign_ip_addr(self, org_id, user_id):
        network_hash = self.server.network_hash
        server_id = self.server.id

        cur_doc = self.get_ip_addr(org_id, user_id)
        if cur_doc:
            return True

        response = self.collection.update_one({
            'network': network_hash,
            'server_id': server_id,
            'user_id': {'$exists': False},
        }, {'$set': {
            'org_id': org_id,
            'user_id': user_id,
        }})
        if bool(response.modified_count):
            return True

        network = ipaddress.IPv4Network(self.server.network)
        if self.server.network_start:
            network_start = ipaddress.IPv4Address(self.server.network_start)
        else:
            network_start = None
        if self.server.network_end:
            network_end = ipaddress.IPv4Address(self.server.network_end)
        else:
            network_end = None

        ip_pool = self.get_ip_pool(network, network_start)
        if not ip_pool:
            return False

        try:
            doc = self.collection.find({
                'network': network_hash,
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
            if network_end and remote_ip_addr > network_end:
                break

            try:
                self.collection.insert_one({
                    '_id': int(remote_ip_addr),
                    'network': network_hash,
                    'server_id': server_id,
                    'org_id': org_id,
                    'user_id': user_id,
                    'address': '%s/%s' % (remote_ip_addr, network.prefixlen),
                })
                return True
            except pymongo.errors.DuplicateKeyError:
                pass

        logger.error('Failed to assign IP, retrying pool', 'server',
            server_id=self.server.id,
            org_id=org_id,
            user_id=user_id,
        )

        ip_pool = self.get_ip_pool(network, network_start)
        if not ip_pool:
            return False

        for remote_ip_addr in ip_pool:
            if network_end and remote_ip_addr > network_end:
                break

            try:
                self.collection.insert_one({
                    '_id': int(remote_ip_addr),
                    'network': network_hash,
                    'server_id': server_id,
                    'org_id': org_id,
                    'user_id': user_id,
                    'address': '%s/%s' % (remote_ip_addr, network.prefixlen),
                })
                return True
            except pymongo.errors.DuplicateKeyError:
                pass

        return False

    def unassign_ip_addr(self, org_id, user_id):
        self.collection.update_one({
            'server_id': self.server.id,
            'network': self.server.network_hash,
            'user_id': user_id,
        }, {'$unset': {
            'org_id': '',
            'user_id': '',
        }})

    def assign_ip_pool_org(self, org_id):
        org = organization.get_by_id(org_id)
        network_hash = self.server.network_hash
        server_id = self.server.id
        org_id = org.id
        ip_pool_avial = True
        pool_end = False

        network = ipaddress.IPv4Network(self.server.network)
        network_start = self.server.network_start
        network_end = self.server.network_end
        if network_start:
            network_start = ipaddress.IPv4Address(network_start)
        if network_end:
            network_end = ipaddress.IPv4Address(network_end)

        ip_pool = self.get_ip_pool(network, network_start)
        if not ip_pool:
            return

        try:
            doc = self.collection.find({
                'network': network_hash,
                'server_id': server_id,
            }).sort('_id', pymongo.DESCENDING)[0]
            if doc:
                last_addr = doc['_id']

                for remote_ip_addr in ip_pool:
                    if int(remote_ip_addr) == last_addr:
                        break
                    if network_end and remote_ip_addr > network_end:
                        break
        except IndexError:
            pass

        bulk = []

        for user in org.iter_users(include_pool=True):
            if user.type != CERT_CLIENT:
                continue

            if ip_pool_avial:
                response = self.collection.update_one({
                    'network': network_hash,
                    'server_id': server_id,
                    'user_id': {'$exists': False},
                }, {'$set': {
                    'org_id': org_id,
                    'user_id': user.id,
                }})
                if bool(response.modified_count):
                    continue
                ip_pool_avial = False

            try:
                remote_ip_addr = next(ip_pool)
                if network_end and remote_ip_addr > network_end:
                    raise StopIteration()
            except StopIteration:
                pool_end = True
                break
            doc_id = int(remote_ip_addr)

            bulk.append(pymongo.UpdateOne({
                '_id': doc_id,
            }, {'$set': {
                '_id': doc_id,
                'network': network_hash,
                'server_id': server_id,
                'org_id': org_id,
                'user_id': user.id,
                'address': '%s/%s' % (remote_ip_addr, network.prefixlen),
            }}, upsert=True))

        if bulk:
            self.collection.bulk_write(bulk)

        if pool_end:
            logger.warning('Failed to assign ip addresses ' +
                'to org, ip pool empty', 'server',
                org_id=org_id,
            )

    def unassign_ip_pool_org(self, org_id):
        self.collection.update_one({
            'server_id': self.server.id,
            'network': self.server.network_hash,
            'org_id': org_id,
        }, {'$unset': {
            'org_id': '',
            'user_id': '',
        }})

    def assign_ip_pool(self, network, network_start,
            network_end, network_hash):
        server_id = self.server.id
        pool_end = False

        network = ipaddress.IPv4Network(network)
        if network_start:
            network_start = ipaddress.IPv4Address(network_start)
        if network_end:
            network_end = ipaddress.IPv4Address(network_end)

        ip_pool = self.get_ip_pool(network, network_start)
        if not ip_pool:
            return

        bulk = []

        for org in self.server.iter_orgs():
            org_id = org.id

            for user in org.iter_users(include_pool=True):
                if user.type != CERT_CLIENT:
                    continue

                try:
                    remote_ip_addr = next(ip_pool)
                    if network_end and remote_ip_addr > network_end:
                        raise StopIteration()
                except StopIteration:
                    pool_end = True
                    break
                doc_id = int(remote_ip_addr)

                bulk.append(pymongo.UpdateOne({
                    '_id': doc_id,
                }, {'$set': {
                    '_id': doc_id,
                    'network': network_hash,
                    'server_id': server_id,
                    'org_id': org_id,
                    'user_id': user.id,
                    'address': '%s/%s' % (remote_ip_addr, network.prefixlen),
                }}, upsert=True))

            if pool_end:
                logger.warning('Failed to assign ip addresses ' +
                    'to server, ip pool empty', 'server',
                    server_id=server_id,
                    org_id=org_id,
                )
                break

        if bulk:
            self.collection.bulk_write(bulk)

    def sync_ip_pool(self):
        server_id = self.server.id

        bulk = []

        bulk.append(pymongo.DeleteMany({
            'server_id': server_id,
            'network': {'$ne': self.server.network_hash},
        }))

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

        for dup_user_ip in dup_user_ips:
            for doc_id in dup_user_ip['ids'][1:]:
                bulk.append(pymongo.UpdateOne({
                    '_id': doc_id,
                }, {'$unset': {
                    'org_id': '',
                    'user_id': '',
                }}))

        user_ids = self.users_collection.find({
            'org_id': {'$in': self.server.organizations},
            'type': CERT_CLIENT,
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
            bulk.append(pymongo.UpdateOne({
                'server_id': server_id,
                'network': self.server.network_hash,
                'user_id': user_id,
            }, {'$unset': {
                'org_id': '',
                'user_id': '',
            }}))

        self.collection.bulk_write(bulk)

        for user_id in user_ids - user_ip_ids:
            doc = self.users_collection.find_one(user_id, {
                'org_id': True,
            })
            if doc:
                if not self.assign_ip_addr(doc['org_id'], user_id):
                    break

    def get_ip_addr(self, org_id, user_id):
        doc = self.collection.find_one({
            'server_id': self.server.id,
            'network': self.server.network_hash,
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
        network = ipaddress.ip_network(doc['address'], strict=False)
        network = str(network.network_address) + '/' + str(network.prefixlen)
        addr6 = utils.ip4to6x64(settings.vpn.ipv6_prefix,
            network, doc['address'])

        yield doc['user_id'], doc['server_id'], \
            doc['address'].split('/')[0], addr6.split('/')[0]
