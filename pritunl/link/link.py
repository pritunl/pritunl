from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo

import hashlib
import base64
import json

class Host(mongo.MongoObject):
    fields = {
        'name',
        'link_id',
        'location_id',
        'secret',
        'status',
        'active',
        'public_address',
        'tunnels',
    }
    fields_default = {
        'status': UNAVAILABLE,
        'active': False,
        'tunnels': 0,
        'routes': [],
    }

    def __init__(self, link=None, location=None, name=None, link_id=None,
            location_id=None, secret=None, status=None, active=None,
            public_address=None, tunnels=None, **kwargs):
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

        if public_address is not None:
            self.public_address = public_address

        if tunnels is not None:
            self.tunnels = tunnels

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('links_hosts')

    def get_state(self):
        links = []
        state = {
            'id': self.id,
            'links': links,
        }
        locations = self.link.get_locations(self.location.id)

        for location in locations:
            host = location.get_active_host()

            links.append({
                'pre_shared_key': self.link.key,
                'right': host.public_address,
                'left_subnets': self.location.routes,
                'right_subnets': location.routes,
            })

        state['hash'] = hashlib.md5(
            json.dumps(state, sort_keys=True)).hexdigest()

        return state


class Location(mongo.MongoObject):
    fields = {
        'name',
        'link_id',
        'hosts',
        'routes',
    }
    fields_default = {
        'status': ACTIVE,
        'routes': [],
    }

    def __init__(self, link=None, name=None, link_id=None, hosts=None,
            routes=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        self.link = link

        if name is not None:
            self.name = name

        if link_id is not None:
            self.link_id = link_id

        if hosts is not None:
            self.hosts = hosts

        if routes is not None:
            self.routes = routes

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('links_locations')

    def get_active_host(self):
        host_id = self.get_active_host_id()
        return Host(link=self.link, location=self, id=host_id)


class Link(mongo.MongoObject):
    fields = {
        'name',
        'status',
        'locations',
        'timeout',
        'key',
    }
    fields_default = {
        'status': OFFLINE,
        'locations': [],
    }

    def __init__(self, name=None, status=None, locations=None,
            timeout=None, key=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        if name is not None:
            self.name = name

        if status is not None:
            self.status = status

        if locations is not None:
            self.locations = locations

        if timeout is not None:
            self.timeout = timeout

        if key is not None:
            self.key = key

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('links')

    def get_location(self, location_id):
        return Location(link=self, id=location_id)

    def iter_locations(self, skip=None):
        cursor = Location.collection.find({
            'link_id': self.id,
        }).sort('name')

        for doc in cursor:
            if skip == doc['_id']:
                continue
            yield Location(link=self, doc=doc)
