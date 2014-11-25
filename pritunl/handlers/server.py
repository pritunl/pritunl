from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import app
from pritunl import auth
from pritunl import host
from pritunl import utils
from pritunl import logger
from pritunl import event
from pritunl import server
from pritunl import organization
from pritunl import auth
from pritunl import ipaddress

import flask
import re
import random
import bson

def _network_invalid():
    return utils.jsonify({
        'error': NETWORK_INVALID,
        'error_msg': NETWORK_INVALID_MSG,
    }, 400)

def _port_invalid():
        return utils.jsonify({
            'error': PORT_INVALID,
            'error_msg': PORT_INVALID_MSG,
        }, 400)

def _dh_param_bits_invalid():
        return utils.jsonify({
            'error': DH_PARAM_BITS_INVALID,
            'error_msg': DH_PARAM_BITS_INVALID_MSG,
        }, 400)

def _local_network_invalid():
    return utils.jsonify({
        'error': LOCAL_NETWORK_INVALID,
        'error_msg': LOCAL_NETWORK_INVALID_MSG,
    }, 400)

def _dns_server_invalid():
    return utils.jsonify({
        'error': DNS_SERVER_INVALID,
        'error_msg': DNS_SERVER_INVALID_MSG,
    }, 400)

def _check_network_overlap(test_network, networks):
    test_start = ipaddress.IPNetwork(test_network).network
    test_end = ipaddress.IPNetwork(test_network).broadcast

    for network in networks:
        net_start = network.network
        net_end = network.broadcast

        if test_start >= net_start and test_start <= net_end:
            return True
        elif test_end >= net_start and test_end <= net_end:
            return True
        elif net_start >= test_start and net_start <= test_end:
            return True
        elif net_end >= test_start and net_end <= test_end:
            return True

    return False

@app.app.route('/server', methods=['GET'])
@app.app.route('/server/<server_id>', methods=['GET'])
@auth.session_auth
def server_get(server_id=None):
    if server_id:
        return utils.jsonify(server.get_dict(server_id))

    servers = []

    for svr in server.iter_servers_dict():
        servers.append(svr)

    return utils.jsonify(servers)

@app.app.route('/server', methods=['POST'])
@app.app.route('/server/<server_id>', methods=['PUT'])
@auth.session_auth
def server_put_post(server_id=None):
    used_resources = server.get_used_resources(server_id)
    network_used = used_resources['networks']
    port_used = used_resources['ports']

    name = None
    name_def = False
    if 'name' in flask.request.json:
        name_def = True
        name = utils.filter_str(flask.request.json['name'])

    network = None
    network_def = False
    if 'network' in flask.request.json:
        network_def = True
        network = flask.request.json['network']

        if network not in settings.vpn.safe_pub_subnets:
            network_split = network.split('/')
            if len(network_split) != 2:
                return _network_invalid()

            address = network_split[0].split('.')
            if len(address) != 4:
                return _network_invalid()
            for i, value in enumerate(address):
                try:
                    address[i] = int(value)
                except ValueError:
                    return _network_invalid()

            try:
                subnet = int(network_split[1])
            except ValueError:
                return _network_invalid()

            if address[0] == 10:
                if address[1] < 0 or address[1] > 255:
                    return _network_invalid()

                if subnet not in (8, 16, 24):
                    return _network_invalid()
            elif address[0] == 172:
                if address[1] < 16 or address[1] > 31:
                    return _network_invalid()

                if subnet not in (16, 24):
                    return _network_invalid()
            elif address[0] == 192 and address[1] == 168:
                if subnet != 24:
                    return _network_invalid()
            else:
                return _network_invalid()

            if address[2] < 0 or address[2] > 255:
                return _network_invalid()

            if address[3] != 0:
                return _network_invalid()

    bind_address = None
    bind_address_def = False
    if 'bind_address' in flask.request.json:
        bind_address_def = True
        bind_address = utils.filter_str(flask.request.json['bind_address'])

    protocol = 'udp'
    protocol_def = False
    if 'protocol' in flask.request.json:
        protocol_def = True
        protocol = flask.request.json['protocol'].lower()

        if protocol not in ('udp', 'tcp'):
            return utils.jsonify({
                'error': PROTOCOL_INVALID,
                'error_msg': PROTOCOL_INVALID_MSG,
            }, 400)

    port = None
    port_def = False
    if 'port' in flask.request.json:
        port_def = True
        port = flask.request.json['port']

        try:
            port = int(port)
        except ValueError:
            return _port_invalid()

        if port < 1 or port > 65535:
            return _port_invalid()

    dh_param_bits = None
    dh_param_bits_def = False
    if 'dh_param_bits' in flask.request.json:
        dh_param_bits_def = True
        dh_param_bits = flask.request.json['dh_param_bits']

        try:
            dh_param_bits = int(dh_param_bits)
        except ValueError:
            return _dh_param_bits_invalid()

        if dh_param_bits not in VALID_DH_PARAM_BITS:
            return _dh_param_bits_invalid()

    mode = None
    mode_def = False
    if 'mode' in flask.request.json:
        mode_def = True
        mode = flask.request.json['mode']

        if mode not in (ALL_TRAFFIC, LOCAL_TRAFFIC, VPN_TRAFFIC):
            return utils.jsonify({
                'error': MODE_INVALID,
                'error_msg': MODE_INVALID_MSG,
            }, 400)

    multi_device = False
    multi_device_def = False
    if 'multi_device' in flask.request.json:
        multi_device_def = True
        multi_device = True if flask.request.json['multi_device'] else False

    local_networks = None
    local_networks_def = False
    if 'local_networks' in flask.request.json:
        local_networks_def = True
        local_networks = flask.request.json['local_networks'] or []

        for local_network in local_networks:
            local_network_split = local_network.split('/')
            if len(local_network_split) != 2:
                return _local_network_invalid()

            address = local_network_split[0].split('.')
            if len(address) != 4:
                return _local_network_invalid()
            for i, value in enumerate(address):
                try:
                    address[i] = int(value)
                except ValueError:
                    return _local_network_invalid()
            if address[0] > 255 or address[0] < 0 or \
                    address[1] > 255 or address[1] < 0 or \
                    address[2] > 255 or address[2] < 0 or \
                    address[3] > 254 or address[3] < 0:
                return _local_network_invalid()

            try:
                subnet = int(local_network_split[1])
            except ValueError:
                return _local_network_invalid()

            if subnet < 1 or subnet > 32:
                return _local_network_invalid()

    dns_servers = None
    dns_servers_def = False
    if 'dns_servers' in flask.request.json:
        dns_servers_def = True
        dns_servers = flask.request.json['dns_servers'] or []

        for dns_server in dns_servers:
            if not re.match(IP_REGEX, dns_server):
                return _dns_server_invalid()

    search_domain = None
    search_domain_def = False
    if 'search_domain' in flask.request.json:
        search_domain_def = True
        search_domain = utils.filter_str(flask.request.json['search_domain'])

    debug = False
    debug_def = False
    if 'debug' in flask.request.json:
        debug_def = True
        debug = True if flask.request.json['debug'] else False

    otp_auth = False
    otp_auth_def = False
    if 'otp_auth' in flask.request.json:
        otp_auth_def = True
        otp_auth = True if flask.request.json['otp_auth'] else False

    lzo_compression = False
    lzo_compression_def = False
    if 'lzo_compression' in flask.request.json:
        lzo_compression_def = True
        lzo_compression = True if flask.request.json[
            'lzo_compression'] else False

    cipher = None
    cipher_def = False
    if 'cipher' in flask.request.json:
        cipher_def = True
        cipher = flask.request.json['cipher']

        if cipher not in CIPHERS:
            return utils.jsonify({
                'error': CIPHER_INVALID,
                'error_msg': CIPHER_INVALID_MSG,
            }, 400)

    jumbo_frames = False
    jumbo_frames_def = False
    if 'jumbo_frames' in flask.request.json:
        jumbo_frames_def = True
        jumbo_frames = True if flask.request.json[
            'jumbo_frames'] else False

    if not server_id:
        if not name_def:
            return utils.jsonify({
                'error': MISSING_PARAMS,
                'error_msg': MISSING_PARAMS_MSG,
            }, 400)

        if not network_def:
            network_def = True
            for i in xrange(5000):
                rand_network = '10.%s.%s.0/24' % (
                    random.randint(15, 250), random.randint(15, 250))
                if not _check_network_overlap(rand_network, network_used):
                    network = rand_network
                    break
            if not network:
                return utils.jsonify({
                    'error': NETWORK_IN_USE,
                    'error_msg': NETWORK_IN_USE_MSG,
                }, 400)

        if not port_def:
            port_def = True
            rand_ports = range(10000, 19999)
            random.shuffle(rand_ports)
            for rand_port in rand_ports:
                if '%s%s' % (rand_port, protocol) not in port_used:
                    port = rand_port
                    break
            if not port:
                return utils.jsonify({
                    'error': PORT_PROTOCOL_IN_USE,
                    'error_msg': PORT_PROTOCOL_IN_USE_MSG,
                }, 400)

        if not dh_param_bits_def:
            dh_param_bits_def = True
            dh_param_bits = settings.vpn.default_dh_param_bits

        if not mode_def:
            mode_def = True
            if local_networks_def and local_networks:
                mode = LOCAL_TRAFFIC
            else:
                mode = ALL_TRAFFIC

    if network_def:
        if _check_network_overlap(network, network_used):
            return utils.jsonify({
                'error': NETWORK_IN_USE,
                'error_msg': NETWORK_IN_USE_MSG,
            }, 400)
    if port_def:
        if '%s%s' % (port, protocol) in port_used:
            return utils.jsonify({
                'error': PORT_PROTOCOL_IN_USE,
                'error_msg': PORT_PROTOCOL_IN_USE_MSG,
            }, 400)

    if not server_id:
        svr = server.new_server(
            name=name,
            network=network,
            bind_address=bind_address,
            port=port,
            protocol=protocol,
            dh_param_bits=dh_param_bits,
            mode=mode,
            multi_device=multi_device,
            local_networks=local_networks,
            dns_servers=dns_servers,
            search_domain=search_domain,
            otp_auth=otp_auth,
            cipher=cipher,
            jumbo_frames=jumbo_frames,
            lzo_compression=lzo_compression,
            debug=debug,
        )
        svr.add_host(settings.local.host_id)
        svr.commit()
    else:
        svr = server.get_by_id(server_id)
        if svr.status == ONLINE:
            return utils.jsonify({
                'error': SERVER_NOT_OFFLINE,
                'error_msg': SERVER_NOT_OFFLINE_SETTINGS_MSG,
            }, 400)
        if name_def:
            svr.name = name
        if network_def:
            svr.network = network
        if bind_address_def:
            svr.bind_address = bind_address
        if port_def:
            svr.port = port
        if protocol_def:
            svr.protocol = protocol
        if dh_param_bits_def and svr.dh_param_bits != dh_param_bits:
            svr.dh_param_bits = dh_param_bits
            svr.generate_dh_param()
        if mode_def:
            svr.mode = mode
        if multi_device_def:
            svr.multi_device = multi_device
        if local_networks_def:
            svr.local_networks = local_networks
        if dns_servers_def:
            svr.dns_servers = dns_servers
        if search_domain_def:
            svr.search_domain = search_domain
        if otp_auth_def:
            svr.otp_auth = otp_auth
        if cipher_def:
            svr.cipher = cipher
        if jumbo_frames_def:
            svr.jumbo_frames = jumbo_frames
        if lzo_compression_def:
            svr.lzo_compression = lzo_compression
        if debug_def:
            svr.debug = debug
        svr.commit(svr.changed)

    logger.LogEntry(message='Created server "%s".' % svr.name)
    event.Event(type=SERVERS_UPDATED)
    for org in svr.iter_orgs():
        event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify(svr.dict())

@app.app.route('/server/<server_id>', methods=['DELETE'])
@auth.session_auth
def server_delete(server_id):
    svr = server.get_by_id(server_id, fields=['_id', 'name', 'organizations'])
    svr.remove()
    logger.LogEntry(message='Deleted server "%s".' % svr.name)
    event.Event(type=SERVERS_UPDATED)
    for org in svr.iter_orgs():
        event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify({})

@app.app.route('/server/<server_id>/organization', methods=['GET'])
@auth.session_auth
def server_org_get(server_id):
    orgs = []
    svr = server.get_by_id(server_id, fields=['_id', 'organizations'])
    for org_doc in svr.get_org_fields(fields=['_id', 'name']):
        org_doc['id'] = org_doc.pop('_id')
        org_doc['server'] = svr.id
        orgs.append(org_doc)

    return utils.jsonify(orgs)

@app.app.route('/server/<server_id>/organization/<org_id>', methods=['PUT'])
@auth.session_auth
def server_org_put(server_id, org_id):
    svr = server.get_by_id(server_id,
        fields=['_id', 'status', 'network', 'organizations'])
    org = organization.get_by_id(org_id, fields=['_id', 'name'])
    if svr.status == ONLINE:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_ATTACH_ORG_MSG,
        }, 400)
    svr.add_org(org)
    svr.commit(svr.changed)
    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_ORGS_UPDATED, resource_id=svr.id)
    event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify({
        'id': org.id,
        'server': svr.id,
        'name': org.name,
    })

@app.app.route('/server/<server_id>/organization/<org_id>',
    methods=['DELETE'])
@auth.session_auth
def server_org_delete(server_id, org_id):
    svr = server.get_by_id(server_id,
        fields=['_id', 'status', 'network', 'primary_organization',
            'primary_user', 'organizations'])
    org = organization.get_by_id(org_id, fields=['_id'])

    if svr.status == ONLINE:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_DETACH_ORG_MSG,
        }, 400)

    svr.remove_org(org)
    svr.commit(svr.changed)

    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_ORGS_UPDATED, resource_id=svr.id)
    event.Event(type=USERS_UPDATED, resource_id=org.id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/host', methods=['GET'])
@auth.session_auth
def server_host_get(server_id):
    hosts = []
    svr = server.get_by_id(server_id, fields=['_id', 'status',
        'replica_count', 'hosts', 'instances'])
    active_hosts = set([x['host_id'] for x in svr.instances])
    hosts_offline = svr.replica_count - len(active_hosts) > 0

    for hst in svr.iter_hosts(fields=['_id', 'name',
            'public_address', 'auto_public_address']):
        if svr.status == ONLINE and hst.id in active_hosts:
            status = ONLINE
        elif svr.status == ONLINE and hosts_offline:
            status = OFFLINE
        else:
            status = None

        hosts.append({
            'id': hst.id,
            'server': svr.id,
            'status': status,
            'name': hst.name,
            'address': hst.public_addr,
        })

    return utils.jsonify(hosts)

@app.app.route('/server/<server_id>/host/<host_id>', methods=['PUT'])
@auth.session_auth
def server_host_put(server_id, host_id):
    svr = server.get_by_id(server_id, fields=['_id', 'hosts'])
    hst = host.get_by_id(host_id, fields=['_id', 'name',
        'public_address', 'auto_public_address'])
    svr.add_host(hst.id)
    svr.commit('hosts')
    event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)

    return utils.jsonify({
        'id': hst.id,
        'server': svr.id,
        'status': OFFLINE,
        'name': hst.name,
        'address': hst.public_addr,
    })

@app.app.route('/server/<server_id>/host/<host_id>', methods=['DELETE'])
@auth.session_auth
def server_host_delete(server_id, host_id):
    svr = server.get_by_id(server_id, fields=['_id', 'hosts'])
    hst = host.get_by_id(host_id, fields=['_id', 'name'])

    svr.remove_host(hst.id)
    svr.commit('hosts')

    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/link', methods=['GET'])
@auth.session_auth
def server_link_get(server_id):
    links = []
    svr = server.get_by_id(server_id, fields=['_id', 'status', 'links',
        'replica_count', 'instances'])
    hosts_offline = svr.replica_count - len(svr.instances) > 0

    if svr.links:
        spec = {
            '_id': {'$in': [x['server_id'] for x in svr.links]},
        }
        for link_svr in server.iter_servers(spec=spec, fields=[
                '_id', 'status', 'name', 'replica_count', 'instances']):
            link_hosts_offline = link_svr.replica_count - len(
                link_svr.instances) > 0
            if svr.status == ONLINE:
                if hosts_offline or link_hosts_offline:
                    status = OFFLINE
                elif link_svr.status == ONLINE:
                    status = ONLINE
                else:
                    status = OFFLINE
            else:
                status = None
            links.append({
                'id': link_svr.id,
                'server': svr.id,
                'status': status,
                'name': link_svr.name,
                'address': None,
            })

    return utils.jsonify(links)

@app.app.route('/server/<server_id>/link/<link_server_id>', methods=['PUT'])
@auth.session_auth
def server_link_put(server_id, link_server_id):
    try:
        server.link_servers(server_id, link_server_id)
    except ServerLinkOnlineError:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_LINK_SERVER_MSG,
        }, 400)

    event.Event(type=SERVER_LINKS_UPDATED, resource_id=server_id)
    event.Event(type=SERVER_LINKS_UPDATED, resource_id=link_server_id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/link/<link_server_id>', methods=['DELETE'])
@auth.session_auth
def server_link_delete(server_id, link_server_id):
    try:
        server.unlink_servers(server_id, link_server_id)
    except ServerLinkOnlineError:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_UNLINK_SERVER_MSG,
        }, 400)

    event.Event(type=SERVER_LINKS_UPDATED, resource_id=server_id)
    event.Event(type=SERVER_LINKS_UPDATED, resource_id=link_server_id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/<operation>', methods=['PUT'])
@auth.session_auth
def server_operation_put(server_id, operation):
    fields = server.dict_fields + ['hosts', 'links', 'replica_count',
        'tls_auth_key'] + (['ca_certificate'] if operation == START else [])

    svr = server.get_by_id(server_id, fields=fields)

    try:
        if operation == START:
            svr.start()
            logger.LogEntry(message='Started server "%s".' % svr.name)
        if operation == STOP:
            svr.stop()
            logger.LogEntry(message='Stopped server "%s".' % svr.name)
        elif operation == RESTART:
            svr.restart()
            logger.LogEntry(message='Restarted server "%s".' % svr.name)
    except:
        event.Event(type=SERVERS_UPDATED)
        raise

    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)
    svr.send_link_events()

    return utils.jsonify(svr.dict())

@app.app.route('/server/<server_id>/output', methods=['GET'])
@auth.session_auth
def server_output_get(server_id):
    return utils.jsonify({
        'id': server_id,
        'output': server.output_get(server_id),
    })

@app.app.route('/server/<server_id>/output', methods=['DELETE'])
@auth.session_auth
def server_output_delete(server_id):
    server.output_clear(server_id)
    return utils.jsonify({})

@app.app.route('/server/<server_id>/link_output', methods=['GET'])
@auth.session_auth
def server_link_output_get(server_id):
    return utils.jsonify({
        'id': server_id,
        'output': server.output_link_get(server_id),
    })

@app.app.route('/server/<server_id>/link_output', methods=['DELETE'])
@auth.session_auth
def server_link_output_delete(server_id):
    server.output_link_clear(server_id)
    return utils.jsonify({})

@app.app.route('/server/<server_id>/bandwidth/<period>', methods=['GET'])
@auth.session_auth
def server_bandwidth_get(server_id, period):
    return utils.jsonify(server.bandwidth_get(server_id, period))
