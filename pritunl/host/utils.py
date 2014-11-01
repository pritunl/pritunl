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

import datetime
import collections

def get_by_id(id, fields=None):
    return Host(id=id, fields=fields)

def iter_hosts(spec=None, fields=None):
    if fields:
        fields = {key: True for key in fields}

    for doc in Host.collection.find(spec or {}, fields).sort('name'):
        yield Host(doc=doc)

def iter_servers_dict():
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
            'client.ignore': False,
        }},
        {'$group': {
            '_id': '$host_id',
            'clients': {'$addToSet': '$client.id'},
        }},
    ])['result']

    hosts_clients = {}
    for doc in response:
        hosts_clients[doc['_id']] = doc['clients']

    org_user_count = organization.get_org_user_count()

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
    ])['result']

    host_orgs = collections.defaultdict(list)
    for doc in response:
        host_orgs[doc['_id']] = doc['organizations']

    for doc in Host.collection.find().sort('name'):
        hst = Host(doc=doc)

        users_online = len(hosts_clients.get(hst.id, ''))

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
