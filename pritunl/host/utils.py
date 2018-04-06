from pritunl.host.host import Host

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import settings
from pritunl import organization
from pritunl import event
from pritunl import utils
from pritunl import logger
from pritunl import mongo

import collections
import random
import socket
import math

def get_by_id(id, fields=None):
    return Host(id=id, fields=fields)

def iter_hosts(spec=None, fields=None, page=None):
    limit = None
    skip = None
    page_count = settings.app.host_page_count

    if spec is None:
        spec = {}

    if fields:
        fields = {key: True for key in fields}

    if page is not None:
        limit = page_count
        skip = page * page_count if page else 0

    cursor = Host.collection.find(spec, fields).sort('name')

    if skip is not None:
        cursor = cursor.skip(page * page_count if page else 0)
    if limit is not None:
        cursor = cursor.limit(limit)

    for doc in cursor:
        yield Host(doc=doc, fields=fields)

def get_host_page_total():
    host_collection = mongo.get_collection('hosts')

    count = host_collection.find({}, {
        '_id': True,
    }).count()

    return int(math.floor(max(0, float(count - 1)) /
        settings.app.host_page_count))

def get_hosts_online():
    host_collection = mongo.get_collection('hosts')

    return host_collection.find({
        'status': ONLINE,
    }, {
        '_id': True,
        'status': True,
    }).count()

def iter_hosts_dict(page=None):
    clients_collection = mongo.get_collection('clients')
    server_collection = mongo.get_collection('servers')

    response = server_collection.aggregate([
        {'$project': {
            'hosts': True,
            'organizations': True,
        }},
        {'$unwind': '$hosts'},
        {'$unwind': '$organizations'},
        {'$group': {
            '_id': '$hosts',
            'organizations': {'$addToSet': '$organizations'},
        }},
    ])

    orgs = set()
    host_orgs = collections.defaultdict(list)
    for doc in response:
        orgs = orgs.union(doc['organizations'])
        host_orgs[doc['_id']] = doc['organizations']

    org_user_count = organization.get_user_count(orgs)

    for hst in iter_hosts(page=page):
        users_online = len(clients_collection.distinct("user_id", {
            'host_id': hst.id,
            'type': CERT_CLIENT,
        }))

        user_count = 0
        for org_id in host_orgs[hst.id]:
            user_count += org_user_count.get(org_id, 0)

        hst.user_count = user_count
        hst.users_online = users_online

        yield hst.dict()

def init():
    if not settings.local.host_id:
        raise ValueError('Host ID undefined')

    settings.local.host = Host(id=settings.local.host_id)

    if not settings.local.host:
        settings.local.host = Host()
        settings.local.host.id = settings.local.host_id

    try:
        settings.local.host.load()
    except NotFound:
        pass

    settings.local.host.version = settings.local.version
    settings.local.host.status = ONLINE
    settings.local.host.users_online = 0
    settings.local.host.start_timestamp = utils.now()
    settings.local.host.ping_timestamp = utils.now()
    if settings.local.public_ip:
        settings.local.host.auto_public_address = settings.local.public_ip
    if settings.local.public_ip6:
        settings.local.host.auto_public_address6 = settings.local.public_ip6

    try:
        settings.local.host.hostname = socket.gethostname()
    except:
        logger.exception('Failed to get hostname', 'host')
        settings.local.host.hostname = None

    if settings.conf.local_address_interface == 'auto':
        try:
            settings.local.host.auto_local_address = utils.get_local_address()
        except:
            logger.exception('Failed to get auto_local_address', 'host')
            settings.local.host.local_address = None

        try:
            settings.local.host.auto_local_address6 = \
                utils.get_local_address6()
        except:
            logger.exception('Failed to get auto_local_address6', 'host')
            settings.local.host.local_address6 = None
    else:
        try:
            settings.local.host.auto_local_address = \
                utils.get_interface_address(
                    str(settings.conf.local_address_interface))
        except:
            logger.exception('Failed to get auto_local_address', 'host',
                interface=settings.conf.local_address_interface)
            settings.local.host.auto_local_address = None

        try:
            settings.local.host.auto_local_address6 = \
                utils.get_interface_address6(
                    str(settings.conf.local_address_interface))
        except:
            logger.exception('Failed to get auto_local_address6', 'host',
                interface=settings.conf.local_address_interface)
            settings.local.host.auto_local_address6 = None

    settings.local.host.auto_instance_id = utils.get_instance_id()
    settings.local.host.local_networks = utils.get_local_networks()

    settings.local.host.commit()
    event.Event(type=HOSTS_UPDATED)

def deinit():
    Host.collection.update({
        '_id': settings.local.host_id,
    }, {'$set': {
        'status': OFFLINE,
        'ping_timestamp': None,
    }})
    event.Event(type=HOSTS_UPDATED)

    logger.LogEntry(message='Web server stopped.')

def get_prefered_hosts(hosts, replica_count):
    return random.sample(hosts, min(replica_count, len(hosts)))
