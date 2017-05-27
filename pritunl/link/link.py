from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import mongo
from pritunl import ipaddress
from pritunl import settings

import hashlib
import json
import datetime
import pymongo

class Host(mongo.MongoObject):
    fields = {
        'name',
        'link_id',
        'location_id',
        'secret',
        'status',
        'active',
        'timeout',
        'priority',
        'ping_timestamp_ttl',
        'public_address',
        'version',
    }
    fields_default = {
        'status': UNAVAILABLE,
        'active': False,
    }

    def __init__(self, link=None, location=None, name=None, link_id=None,
            location_id=None, secret=None, status=None, active=None,
            timeout=None, priority=None, ping_timestamp_ttl=None,
            public_address=None, version=None, tunnels=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        self.link = link
        self.location = location

        if name is not None:
            self.name = name

        if link_id is not None:
            self.link_id = link_id

        if location_id is not None:
            self.location_id = location_id

        if secret is not None:
            self.secret = secret

        if status is not None:
            self.status = status

        if active is not None:
            self.active = active

        if timeout is not None:
            self.timeout = timeout

        if priority is not None:
            self.priority = priority

        if ping_timestamp_ttl is not None:
            self.ping_timestamp_ttl = ping_timestamp_ttl

        if public_address is not None:
            self.public_address = public_address

        if version is not None:
            self.version = version

        if tunnels is not None:
            self.tunnels = tunnels

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('links_hosts')

    @property
    def is_available(self):
        if self.status != AVAILABLE or \
                not self.ping_timestamp_ttl or \
                utils.now() > self.ping_timestamp_ttl:
            return False
        return True

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'link_id': self.link_id,
            'location_id': self.location_id,
            'status': ACTIVE if self.active and \
                self.link.status == ONLINE else self.status,
            'timeout': self.timeout,
            'priority': self.priority,
            'ping_timestamp_ttl': self.ping_timestamp_ttl,
            'public_address': self.public_address,
            'version': self.version,
        }

    def check_available(self):
        if self.is_available:
            return True

        response = self.collection.update({
            '_id': self.id,
            'ping_timestamp_ttl': self.ping_timestamp_ttl,
        }, {'$set': {
            'status': UNAVAILABLE,
            'active': False,
            'ping_timestamp_ttl': None,
        }})

        if response['updatedExisting']:
            self.active = False
            self.status = UNAVAILABLE
            self.ping_timestamp_ttl = None
            return False

        return True

    def load_link(self):
        self.link = Link(id=self.link_id)
        self.location = Location(link=self.link, id=self.location_id)

    def generate_secret(self):
        self.secret = utils.rand_str(32)

    def get_uri(self):
        return 'pritunl://%s:%s@' % (self.id, self.secret)

    def set_active(self):
        response = self.collection.update({
            '_id': self.id,
            'status': AVAILABLE,
        }, {'$set': {
            'active': True,
        }})
        if not response['updatedExisting']:
            return False

        Host.collection.update_many({
            '_id': {'$ne': self.id},
            'location_id': self.location_id,
        }, {'$set': {
            'active': False,
        }})

        return True

    def get_state(self):
        self.status = AVAILABLE
        self.ping_timestamp_ttl = utils.now() + datetime.timedelta(
            seconds=self.timeout or settings.vpn.link_timeout)
        self.commit(('public_address', 'status', 'ping_timestamp_ttl'))

        links = []
        state = {
            'id': self.id,
            'links': links,
        }
        active_host = self.location.get_active_host()

        if self.link.status == ONLINE and active_host and \
                active_host.id == self.id:
            locations = self.link.iter_locations(self.location.id, sort=False)

            for location in locations:
                active_host = location.get_active_host()
                if not active_host:
                    continue

                left_subnets = []
                for route in self.location.routes.values():
                    left_subnets.append(route['network'])

                right_subnets = []
                for route in location.routes.values():
                    right_subnets.append(route['network'])

                links.append({
                    'pre_shared_key': self.link.key,
                    'right': active_host.public_address,
                    'left_subnets': left_subnets,
                    'right_subnets': right_subnets,
                })

        state['hash'] = hashlib.md5(json.dumps(
            state,
            sort_keys=True,
            default=lambda x: str(x),
        )).hexdigest()

        return state

class Location(mongo.MongoObject):
    fields = {
        'name',
        'link_id',
        'routes',
        'location',
    }
    fields_default = {
        'routes': {},
    }

    def __init__(self, link=None, name=None, link_id=None, routes=None,
            **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        self.link = link

        if name is not None:
            self.name = name

        if link_id is not None:
            self.link_id = link_id

        if routes is not None:
            self.routes = routes

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('links_locations')

    def dict(self):
        hosts = []
        for hst in self.iter_hosts():
            hosts.append(hst.dict())

        routes = []
        for route_id, route in self.routes.items():
            route['id'] = route_id
            route['link_id'] = self.link_id
            route['location_id'] = self.id
            routes.append(route)

        return {
            'id': self.id,
            'name': self.name,
            'link_id': self.link_id,
            'hosts': hosts,
            'routes': routes,
            'location': self.location,
        }

    def remove(self):
        Host.collection.remove({
            'location_id': self.id,
        })
        mongo.MongoObject.remove(self)

    def add_route(self, network):
        try:
            network = str(ipaddress.IPNetwork(network))
        except ValueError:
            raise NetworkInvalid('Network address is invalid')

        network_id = hashlib.md5(network).hexdigest()
        self.routes[network_id] = {
            'network': network,
        }

        return network_id

    def remove_route(self, network_id):
        self.routes.pop(network_id)

    def get_host(self, host_id):
        return Host(link=self.link, location=self, id=host_id)

    def iter_hosts(self):
        cursor = Host.collection.find({
            'location_id': self.id,
        }).sort('name')

        for doc in cursor:
            yield Host(link=self.link, location=self, doc=doc)

    def get_active_host(self):
        if self.link.status != ONLINE:
            return

        doc = Host.collection.find_one({
            'location_id': self.id,
            'status': AVAILABLE,
            'active': True,
        })

        if doc:
            return Host(link=self.link, location=self, doc=doc)

        cursor = Host.collection.find({
            'location_id': self.id,
            'status': AVAILABLE,
            'active': False,
        }, {
            '_id': True,
        }).sort('priority', pymongo.DESCENDING).limit(1)

        doc = None
        for doc in cursor:
            break

        if not doc:
            return

        doc_id = doc['_id']
        response = Host.collection.update({
            '_id': doc_id,
            'status': AVAILABLE,
            'active': False,
        }, {'$set': {
            'active': True,
        }})
        if not response['updatedExisting']:
            return

        Host.collection.update_many({
            '_id': {'$ne': doc_id},
            'location_id': self.id,
        }, {'$set': {
            'active': False,
        }})

        return Host(link=self.link, location=self, doc=doc)


class Link(mongo.MongoObject):
    fields = {
        'name',
        'status',
        'key',
    }
    fields_default = {
        'status': OFFLINE,
    }

    def __init__(self, name=None, status=None, timeout=None,
            key=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        if name is not None:
            self.name = name

        if status is not None:
            self.status = status

        if timeout is not None:
            self.timeout = timeout

        if key is not None:
            self.key = key

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('links')

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
        }

    def remove(self):
        Host.collection.remove({
            'link_id': self.id,
        })
        Location.collection.remove({
            'link_id': self.id,
        })
        mongo.MongoObject.remove(self)

    def generate_key(self):
        self.key = utils.rand_str(32)

    def get_location(self, location_id):
        return Location(link=self, id=location_id)

    def iter_locations(self, skip=None, sort=True):
        spec = {
            'link_id': self.id,
        }

        if skip:
            spec['_id'] = {'$ne': skip}

        if sort:
            cursor = Location.collection.find(spec).sort('name')
        else:
            cursor = Location.collection.find(spec)

        for doc in cursor:
            yield Location(link=self, doc=doc)
