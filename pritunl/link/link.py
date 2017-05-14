from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import utils
from pritunl import mongo
from pritunl import ipaddress

import hashlib
import json

class Host(mongo.MongoObject):
    fields = {
        'name',
        'link_id',
        'location_id',
        'secret',
        'status',
        'active',
        'ping_timestamp',
        'public_address',
    }
    fields_default = {
        'status': UNAVAILABLE,
        'active': False,
    }

    def __init__(self, link=None, location=None, name=None, link_id=None,
            location_id=None, secret=None, status=None, active=None,
            ping_timestamp=None, public_address=None, tunnels=None, **kwargs):
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

        if ping_timestamp is not None:
            self.ping_timestamp = ping_timestamp

        if public_address is not None:
            self.public_address = public_address

        if tunnels is not None:
            self.tunnels = tunnels

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('links_hosts')

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'link_id': self.link_id,
            'location_id': self.location_id,
            'secret': self.secret,
            'status': ACTIVE if self.active else self.status,
            'ping_timestamp': self.ping_timestamp,
            'public_address': self.public_address,
        }

    def generate_secret(self):
        self.secret = utils.rand_str(32)

    def get_uri(self, hostname):
        return 'pritunl://%s:%s@%s' % (self.id, self.secret, hostname)

    def get_state(self):
        self.status = AVAILABLE
        self.ping_timestamp = utils.now()
        self.commit(('status', 'ping_timestamp'))

        links = []
        state = {
            'id': self.id,
            'links': links,
        }

        if self.link.status != ONLINE:
            return state

        active_host = self.location.get_active_host()
        if active_host and active_host.id == self.id:
            locations = self.link.iter_locations(self.location.id)

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
        'quality',
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
            'quality': self.quality,
        }

    def add_route(self, network):
        try:
            network = str(ipaddress.IPNetwork(network))
        except ValueError:
            raise NetworkInvalid('Network address is invalid')

        network_id = network.encode('hex')

        self.routes[network_id] = {
            'network': network,
        }

    def get_host(self, host_id):
        return Host(link=self.link, location=self, id=host_id)

    def iter_hosts(self):
        cursor = Host.collection.find({
            'location_id': self.id,
        }).sort('name')

        for doc in cursor:
            yield Host(link=self, doc=doc)

    def get_active_host(self):
        doc = Host.collection.find_one({
            'location_id': self.id,
            'active': True,
        })

        if doc:
            return Host(link=self.link, location=self, doc=doc)

        doc = Host.collection.find_and_modify({
            'location_id': self.id,
            'status': AVAILABLE,
        }, {
            '$set': {
                'active': True,
            },
        })
        if not doc:
            return

        Host.collection.update_many({
            '_id': {'$ne': doc['_id']},
            'location_id': self.id,
        }, {
            '$set': {
                'active': False,
            },
        })

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

    def generate_key(self):
        self.key = utils.rand_str(32)

    def get_location(self, location_id):
        return Location(link=self, id=location_id)

    def iter_locations(self, skip=None):
        spec = {
            'link_id': self.id,
        }

        if skip:
            spec['_id'] = {'$ne': skip}

        cursor = Location.collection.find(spec).sort('name')

        for doc in cursor:
            yield Location(link=self, doc=doc)
