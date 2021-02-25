from pritunl.server.output import ServerOutput
from pritunl.server.output_link import ServerOutputLink
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.server import Server, dict_fields

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import transaction
from pritunl import mongo
from pritunl import ipaddress
from pritunl import settings

import math

def new_server(**kwargs):
    server = Server(**kwargs)
    server.initialize()
    return server

def get_by_id(id, fields=None):
    return Server(id=id, fields=fields)

def get_dict(id):
    return Server(id=id, fields=dict_fields).dict()

def get_online_ipv6_count():
    return Server.collection.find({
        'status': ONLINE,
        'ipv6': True,
    }).count()

def get_used_resources(ignore_server_id):
    response = Server.collection.aggregate(([
        {'$match': {
            '_id': {'$ne': ignore_server_id},
        }},
    ] if ignore_server_id else []) + [
        {'$project': {
            'network': True,
            'network_wg': True,
            'interface': True,
            'port_protocol': {'$concat': [
                {'$substr': ['$port', 0, 5]},
                '$protocol',
            ]},
            'port_protocol_wg': {'$concat': [
                {'$substr': ['$port_wg', 0, 5]},
                'udp',
            ]},
        }},
        {'$group': {
            '_id': None,
            'networks': {'$addToSet': '$network'},
            'networks_wg': {'$addToSet': '$network_wg'},
            'interfaces': {'$addToSet': '$interface'},
            'ports': {'$addToSet': '$port_protocol'},
            'ports_wg': {'$addToSet': '$port_protocol_wg'},
        }},
    ])

    used_resources = None
    for used_resources in response:
        break

    if used_resources:
        used_resources.pop('_id')
    else:
        used_resources = {
            'networks': set(),
            'networks_wg': set(),
            'interfaces': set(),
            'ports': set(),
            'ports_wg': set(),
        }

    ports = set(used_resources['ports'] or [])
    ports_wg = set([_f for _f in used_resources['ports_wg'] if _f])
    try:
        ports_wg.remove('udp')
    except KeyError:
        pass
    ports = ports.union(ports_wg)

    networks = set(used_resources['networks'] or [])
    networks_wg = set([_f for _f in used_resources['networks_wg'] if _f])
    networks = networks.union(networks_wg)

    return {
        'networks': {ipaddress.ip_network(x, strict=False) for x in networks},
        'interfaces': set(used_resources['interfaces'] or []),
        'ports': ports,
    }

def iter_servers(spec=None, fields=None, page=None):
    limit = None
    skip = None
    page_count = settings.app.server_page_count

    if spec is None:
        spec = {}

    if fields:
        fields = {key: True for key in fields}

    if page is not None:
        limit = page_count
        skip = page * page_count if page else 0

    cursor = Server.collection.find(spec, fields).sort('name')

    if skip is not None:
        cursor = cursor.skip(page * page_count if page else 0)
    if limit is not None:
        cursor = cursor.limit(limit)

    for doc in cursor:
        yield Server(doc=doc, fields=fields)

def iter_servers_dict(page=None):
    fields = {key: True for key in dict_fields}

    for svr in iter_servers(fields=fields, page=page):
        yield svr.dict()

def get_server_page_total():
    org_collection = mongo.get_collection('servers')

    count = org_collection.find({}, {
        '_id': True,
    }).count()

    return int(math.floor(max(0, float(count - 1)) /
        settings.app.server_page_count))

def output_get(server_id):
    return ServerOutput(server_id).get_output()

def output_clear(server_id):
    ServerOutput(server_id).clear_output()

def output_link_get(server_id):
    return ServerOutputLink(server_id).get_output()

def output_link_clear(server_id):
    svr = get_by_id(server_id, fields=['_id', 'links'])
    ServerOutputLink(server_id).clear_output(
        [x['server_id'] for x in svr.links])

def bandwidth_get(server_id, period):
    return ServerBandwidth(server_id).get_period(period)

def bandwidth_random_get(server_id, period):
    return ServerBandwidth(server_id).get_period_random(period)

def link_servers(server_id, link_server_id, use_local_address=False):
    if server_id == link_server_id:
        raise TypeError('Server id must be different then link server id')

    hosts = set()
    routes = set()
    for svr, link_id in (
                (get_by_id(server_id), link_server_id),
                (get_by_id(link_server_id), server_id),
            ):
        has_link = False
        if svr.links:
            for link in svr.links:
                if link['server_id'] == link_id:
                    has_link = True

        if not has_link:
            if not svr.links:
                svr.links = []

            svr.links.append({
                'server_id': link_id,
                'user_id': None,
                'use_local_address': use_local_address,
            })

        err, err_msg = svr.validate_conf()
        if err:
            return err, err_msg

        hosts_set = set(svr.hosts)
        if hosts & hosts_set:
            return SERVER_LINK_COMMON_HOST, SERVER_LINK_COMMON_HOST_MSG
        hosts.update(hosts_set)

        routes_set = set()
        for route in svr.get_routes():
            if route['network'] != '0.0.0.0/0':
                routes_set.add(route['network'])
        if routes & routes_set:
            return SERVER_LINK_COMMON_ROUTE, SERVER_LINK_COMMON_ROUTE_MSG
        routes.update(routes_set)

    tran = transaction.Transaction()
    collection = tran.collection('servers')

    collection.update({
        '_id': server_id,
        'links.server_id': {'$ne': link_server_id},
    }, {'$push': {
        'links': {
            'server_id': link_server_id,
            'user_id': None,
            'use_local_address': use_local_address,
        },
    }})

    collection.update({
        '_id': link_server_id,
        'links.server_id': {'$ne': server_id},
    }, {'$addToSet': {
        'links': {
            'server_id': server_id,
            'user_id': None,
            'use_local_address': use_local_address,
        },
    }})

    tran.commit()

    return None, None

def unlink_servers(server_id, link_server_id):
    collection = mongo.get_collection('servers')

    spec = {
        '_id': {'$in': [server_id, link_server_id]},
    }
    project = {
        '_id': True,
        'status': True,
    }

    for doc in collection.find(spec, project):
        if doc['status'] == ONLINE:
            raise ServerLinkOnlineError('Server must be offline to unlink')

    tran = transaction.Transaction()
    collection = tran.collection('servers')

    collection.update({
        '_id': server_id,
    }, {'$pull': {
        'links': {'server_id': link_server_id},
    }})

    collection.update({
        '_id': link_server_id,
    }, {'$pull': {
        'links': {'server_id': server_id},
    }})

    tran.commit()
