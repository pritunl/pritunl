from pritunl.host.host import Host

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
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
    org_collection = mongo.get_collection('hosts')

    count = org_collection.find({}, {
        '_id': True,
    }).count()

    return int(math.floor(max(0, float(count - 1)) /
        settings.app.host_page_count))

def iter_hosts_dict(page=None):
    server_collection = mongo.get_collection('servers')

    response = server_collection.aggregate([
        {'$project': {
            'host_id': '$instances.host_id',
            'client': '$instances.clients',
        }},
        {'$unwind': '$host_id'},
        {'$unwind': '$client'},
        {'$unwind': '$client'},
        {'$match': {
            'client.type': CERT_CLIENT,
        }},
        {'$group': {
            '_id': '$host_id',
            'clients': {'$addToSet': '$client.id'},
        }},
    ])

    hosts_clients = {}
    for doc in response:
        hosts_clients[doc['_id']] = doc['clients']

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
        users_online = len(hosts_clients.get(hst.id, []))

        user_count = 0
        for org_id in host_orgs[hst.id]:
            user_count += org_user_count.get(org_id, 0)

        hst.user_count = user_count
        hst.users_online = users_online

        yield hst.dict()

def init():
    settings.local.host = Host()

    try:
        settings.local.host.load()
    except NotFound:
        pass

    settings.local.host.status = ONLINE
    settings.local.host.users_online = 0
    settings.local.host.start_timestamp = utils.now()
    settings.local.host.ping_timestamp = utils.now()
    if settings.local.public_ip:
        settings.local.host.auto_public_address = settings.local.public_ip

    try:
        settings.local.host.hostname = socket.gethostname()
    except:
        logger.exception('Failed to get hostname', 'host')
        settings.local.host.hostname = None

    if settings.conf.local_address_interface == 'auto':
        try:
            settings.local.host.local_address = socket.gethostbyname(
                socket.gethostname())
        except:
            logger.exception('Failed to get local_address auto', 'host')
            settings.local.host.local_address = None
    else:
        try:
            settings.local.host.local_address = utils.get_interface_address(
                str(settings.conf.local_address_interface))
        except:
            logger.exception('Failed to get local_address', 'host',
                interface=settings.conf.local_address_interface)
            settings.local.host.local_address = None

    settings.local.host.commit()
    event.Event(type=HOSTS_UPDATED)

def deinit():
    Host.collection.update({
        '_id': settings.local.host.id,
    }, {'$set': {
        'status': OFFLINE,
        'ping_timestamp': None,
    }})
    event.Event(type=HOSTS_UPDATED)

    if settings.conf.debug:
        logger.LogEntry(message='Web debug server stopped.')
    else:
        logger.LogEntry(message='Web server stopped.')

def get_prefered_hosts(hosts, replica_count):
    return random.sample(hosts, min(replica_count, len(hosts)))
