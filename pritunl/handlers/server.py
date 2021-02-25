from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import settings
from pritunl import app
from pritunl import host
from pritunl import utils
from pritunl import logger
from pritunl import event
from pritunl import server
from pritunl import organization
from pritunl import auth
from pritunl import ipaddress

import flask
import random

def _network_invalid():
    return utils.jsonify({
        'error': NETWORK_INVALID,
        'error_msg': NETWORK_INVALID_MSG,
    }, 400)

def _network_wg_invalid():
    return utils.jsonify({
        'error': NETWORK_WG_INVALID,
        'error_msg': NETWORK_WG_INVALID_MSG,
    }, 400)

def _port_invalid():
    return utils.jsonify({
        'error': PORT_INVALID,
        'error_msg': PORT_INVALID_MSG,
    }, 400)

def _port_wg_invalid():
    return utils.jsonify({
        'error': PORT_WG_INVALID,
        'error_msg': PORT_WG_INVALID_MSG,
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
    test_net = ipaddress.ip_network(test_network)
    test_start = test_net.network_address
    test_end = test_net.broadcast_address

    for network in networks:
        net_start = network.network_address
        net_end = network.broadcast_address

        if test_start >= net_start and test_start <= net_end:
            return True
        elif test_end >= net_start and test_end <= net_end:
            return True
        elif net_start >= test_start and net_start <= test_end:
            return True
        elif net_end >= test_start and net_end <= test_end:
            return True

    return False

def _check_network_private(test_network):
    test_net = ipaddress.ip_network(test_network)
    test_start = test_net.network_address
    test_end = test_net.broadcast_address

    for network in settings.vpn.safe_priv_subnets:
        network = ipaddress.ip_network(network)
        net_start = network.network_address
        net_end = network.broadcast_address

        if test_start >= net_start and test_end <= net_end:
            return True

    return False

def _check_network_range(test_network, start_addr, end_addr):
    test_net = ipaddress.ip_network(test_network)
    start_addr = ipaddress.ip_address(start_addr)
    end_addr = ipaddress.ip_address(end_addr)

    return all((
        start_addr != test_net.network_address,
        end_addr != test_net.broadcast_address,
        start_addr < end_addr,
        start_addr in test_net,
        end_addr in test_net,
    ))

@app.app.route('/server', methods=['GET'])
@app.app.route('/server/<server_id>', methods=['GET'])
@auth.session_auth
def server_get(server_id=None):
    if server_id:
        if settings.app.demo_mode:
            resp = utils.demo_get_cache()
            if resp:
                return utils.jsonify(resp)

        resp = server.get_dict(server_id)
        if settings.app.demo_mode:
            utils.demo_set_cache(resp)
        return utils.jsonify(resp)

    servers = []
    page = flask.request.args.get('page', None)
    page = int(page) if page else page

    if settings.app.demo_mode:
        resp = utils.demo_get_cache(page)
        if resp:
            return utils.jsonify(resp)

    for svr in server.iter_servers_dict(page=page):
        servers.append(svr)

    if page is not None:
        resp = {
            'page': page,
            'page_total': server.get_server_page_total(),
            'servers': servers,
        }
    else:
        resp = servers

    if settings.app.demo_mode:
        utils.demo_set_cache(resp, page)
    return utils.jsonify(resp)

@app.app.route('/server', methods=['POST'])
@app.app.route('/server/<server_id>', methods=['PUT'])
@auth.session_auth
def server_put_post(server_id=None):
    if settings.app.demo_mode:
        return utils.demo_blocked()

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
    if 'network' in flask.request.json and \
            flask.request.json['network'] != '':
        network_def = True
        network = flask.request.json['network'].strip()

        try:
            if not _check_network_private(network):
                return _network_invalid()
        except (ipaddress.AddressValueError, ValueError):
            return _network_invalid()

    wg = None
    wg_def = False
    if 'wg' in flask.request.json:
        wg_def = True
        wg = True if flask.request.json['wg'] else False

    network_wg = None
    network_wg_def = False
    if wg and 'network_wg' in flask.request.json and \
            flask.request.json['network_wg'] != '':
        network_wg_def = True
        network_wg = flask.request.json['network_wg'].strip()

        try:
            if not _check_network_private(network_wg):
                return _network_wg_invalid()
        except (ipaddress.AddressValueError, ValueError):
            return _network_wg_invalid()
    elif not wg:
        network_wg_def = True

    network_mode = None
    network_mode_def = False
    if 'network_mode' in flask.request.json:
        network_mode_def = True
        network_mode = flask.request.json['network_mode']

    network_start = None
    network_start_def = False
    if 'network_start' in flask.request.json:
        network_start_def = True
        network_start = flask.request.json['network_start']

    network_end = None
    network_end_def = False
    if 'network_end' in flask.request.json:
        network_end_def = True
        network_end = flask.request.json['network_end']

    restrict_routes = None
    restrict_routes_def = False
    if 'restrict_routes' in flask.request.json:
        restrict_routes_def = True
        restrict_routes = True if flask.request.json['restrict_routes'] \
            else False

    ipv6 = None
    ipv6_def = False
    if 'ipv6' in flask.request.json:
        ipv6_def = True
        ipv6 = True if flask.request.json['ipv6'] else False

    ipv6_firewall = None
    ipv6_firewall_def = False
    if 'ipv6_firewall' in flask.request.json:
        ipv6_firewall_def = True
        ipv6_firewall = True if flask.request.json['ipv6_firewall'] else False

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
    if 'port' in flask.request.json and flask.request.json['port'] != 0:
        port_def = True
        port = flask.request.json['port']

        try:
            port = int(port)
        except ValueError:
            return _port_invalid()

        if port < 1 or port > 65535:
            return _port_invalid()

    port_wg = None
    port_wg_def = False
    if wg and 'port_wg' in flask.request.json and \
            flask.request.json['port_wg'] != 0:
        port_wg_def = True
        port_wg = flask.request.json['port_wg']

        try:
            port_wg = int(port_wg)
        except ValueError:
            return _port_wg_invalid()

        if port_wg < 1 or port_wg > 65535:
            return _port_wg_invalid()
    elif not wg:
        port_wg_def = True

    dh_param_bits = None
    dh_param_bits_def = False
    if flask.request.json.get('dh_param_bits'):
        dh_param_bits_def = True
        dh_param_bits = flask.request.json['dh_param_bits']

        try:
            dh_param_bits = int(dh_param_bits)
        except ValueError:
            return _dh_param_bits_invalid()

        if dh_param_bits not in VALID_DH_PARAM_BITS:
            return _dh_param_bits_invalid()

    groups = None
    groups_def = False
    if 'groups' in flask.request.json:
        groups_def = True
        groups = flask.request.json['groups'] or []
        for i, group in enumerate(groups):
            groups[i] = utils.filter_str(group)
        groups = list(set(groups))

    multi_device = False
    multi_device_def = False
    if 'multi_device' in flask.request.json:
        multi_device_def = True
        multi_device = True if flask.request.json['multi_device'] else False

    dns_servers = None
    dns_servers_def = False
    if 'dns_servers' in flask.request.json:
        dns_servers_def = True
        dns_servers = flask.request.json['dns_servers'] or []

        for dns_server in dns_servers:
            try:
                ipaddress.ip_address(dns_server)
            except (ipaddress.AddressValueError, ValueError):
                return _dns_server_invalid()

    search_domain = None
    search_domain_def = False
    if 'search_domain' in flask.request.json:
        search_domain_def = True
        search_domain = flask.request.json['search_domain']
        if search_domain:
            search_domain = ', '.join([utils.filter_str(x.strip()) for x in
                search_domain.split(',')])
        else:
            search_domain = None

    inter_client = True
    inter_client_def = False
    if 'inter_client' in flask.request.json:
        inter_client_def = True
        inter_client = True if flask.request.json['inter_client'] else False

    ping_interval = None
    ping_interval_def = False
    if 'ping_interval' in flask.request.json:
        ping_interval_def = True
        ping_interval = int(flask.request.json['ping_interval'] or 10)

    ping_timeout = None
    ping_timeout_def = False
    if 'ping_timeout' in flask.request.json:
        ping_timeout_def = True
        ping_timeout = int(flask.request.json['ping_timeout'] or 60)

    link_ping_interval = None
    link_ping_interval_def = False
    if 'link_ping_interval' in flask.request.json:
        link_ping_interval_def = True
        link_ping_interval = int(
            flask.request.json['link_ping_interval'] or 1)

    link_ping_timeout = None
    link_ping_timeout_def = False
    if 'link_ping_timeout' in flask.request.json:
        link_ping_timeout_def = True
        link_ping_timeout = int(flask.request.json['link_ping_timeout'] or 5)

    inactive_timeout = None
    inactive_timeout_def = False
    if 'inactive_timeout' in flask.request.json:
        inactive_timeout_def = True
        inactive_timeout = int(
            flask.request.json['inactive_timeout'] or 0) or None

    session_timeout = None
    session_timeout_def = False
    if 'session_timeout' in flask.request.json:
        session_timeout_def = True
        session_timeout = int(
            flask.request.json['session_timeout'] or 0) or None

    allowed_devices = None
    allowed_devices_def = False
    if 'allowed_devices' in flask.request.json:
        allowed_devices_def = True
        allowed_devices = flask.request.json['allowed_devices'] or None

    max_clients = None
    max_clients_def = False
    if 'max_clients' in flask.request.json:
        max_clients_def = True
        max_clients = flask.request.json['max_clients']
        if max_clients:
            max_clients = int(max_clients)
        else:
            max_clients = 2000

    max_devices = None
    max_devices_def = False
    if 'max_devices' in flask.request.json:
        max_devices_def = True
        max_devices = flask.request.json['max_devices']
        if max_devices:
            max_devices = int(max_devices)
        else:
            max_devices = 0

    replica_count = None
    replica_count_def = False
    if 'replica_count' in flask.request.json:
        replica_count_def = True
        replica_count = flask.request.json['replica_count']
        if replica_count:
            replica_count = int(replica_count)
        if not replica_count:
            replica_count = 1

    vxlan = True
    vxlan_def = False
    if 'vxlan' in flask.request.json:
        vxlan_def = True
        vxlan = True if flask.request.json['vxlan'] else False

    dns_mapping = False
    dns_mapping_def = False
    if 'dns_mapping' in flask.request.json:
        dns_mapping_def = True
        dns_mapping = True if flask.request.json['dns_mapping'] else False

    debug = False
    debug_def = False
    if 'debug' in flask.request.json:
        debug_def = True
        debug = True if flask.request.json['debug'] else False

    pre_connect_msg = None
    pre_connect_msg_def = False
    if 'pre_connect_msg' in flask.request.json:
        pre_connect_msg_def = True
        if flask.request.json['pre_connect_msg']:
            pre_connect_msg = flask.request.json['pre_connect_msg'].strip()

    otp_auth = False
    otp_auth_def = False
    if 'otp_auth' in flask.request.json:
        otp_auth_def = True
        otp_auth = True if flask.request.json['otp_auth'] else False

    mss_fix = None
    mss_fix_def = False
    if 'mss_fix' in flask.request.json:
        mss_fix_def = True
        mss_fix = flask.request.json['mss_fix'] or None
        if mss_fix:
            mss_fix = int(mss_fix) or None

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

    hash = None
    hash_def = False
    if 'hash' in flask.request.json:
        hash_def = True
        hash = flask.request.json['hash']

        if hash not in HASHES:
            return utils.jsonify({
                'error': HASH_INVALID,
                'error_msg': HASH_INVALID_MSG,
            }, 400)

    block_outside_dns = False
    block_outside_dns_def = False
    if 'block_outside_dns' in flask.request.json:
        block_outside_dns_def = True
        block_outside_dns = True if flask.request.json[
            'block_outside_dns'] else False

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
            rand_range = list(range(215, 250))
            rand_range_low = list(range(15, 215))
            random.shuffle(rand_range)
            random.shuffle(rand_range_low)
            rand_range += rand_range_low
            for i in rand_range:
                rand_network = '192.168.%s.0/24' % i
                if not _check_network_overlap(rand_network, network_used):
                    network = rand_network
                    break
            if not network:
                return utils.jsonify({
                    'error': NETWORK_IN_USE,
                    'error_msg': NETWORK_IN_USE_MSG,
                }, 400)

        if wg and not network_wg_def:
            network_used.add(ipaddress.ip_network(network))

            network_wg_def = True
            rand_range = list(range(215, 250))
            rand_range_low = list(range(15, 215))
            random.shuffle(rand_range)
            random.shuffle(rand_range_low)
            rand_range += rand_range_low
            for i in rand_range:
                rand_network_wg = '192.168.%s.0/24' % i
                if not _check_network_overlap(
                        rand_network_wg, network_used):
                    network_wg = rand_network_wg
                    break
            if not network_wg:
                return utils.jsonify({
                    'error': NETWORK_WG_IN_USE,
                    'error_msg': NETWORK_WG_IN_USE_MSG,
                }, 400)

        if not port_def:
            port_def = True
            rand_ports = list(range(10000, 19999))
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

        if wg and not port_wg_def:
            port_used.add(port)

            port_wg_def = True
            rand_port_wgs = list(range(10000, 19999))
            random.shuffle(rand_port_wgs)
            for rand_port_wg in rand_port_wgs:
                if '%s%s' % (rand_port_wg, protocol) not in port_used:
                    port_wg = rand_port_wg
                    break
            if not port_wg:
                return utils.jsonify({
                    'error': PORT_WG_IN_USE,
                    'error_msg': PORT_WG_IN_USE_MSG,
                }, 400)

        if not dh_param_bits_def:
            dh_param_bits_def = True
            dh_param_bits = settings.vpn.default_dh_param_bits

    changed = None

    if not server_id:
        svr = server.new_server(
            name=name,
            network=network,
            network_wg=network_wg,
            groups=groups,
            network_mode=network_mode,
            network_start=network_start,
            network_end=network_end,
            restrict_routes=restrict_routes,
            wg=wg,
            ipv6=ipv6,
            ipv6_firewall=ipv6_firewall,
            bind_address=bind_address,
            port=port,
            port_wg=port_wg,
            protocol=protocol,
            dh_param_bits=dh_param_bits,
            multi_device=multi_device,
            dns_servers=dns_servers,
            search_domain=search_domain,
            otp_auth=otp_auth,
            cipher=cipher,
            hash=hash,
            block_outside_dns=block_outside_dns,
            jumbo_frames=jumbo_frames,
            lzo_compression=lzo_compression,
            inter_client=inter_client,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            link_ping_interval=link_ping_interval,
            link_ping_timeout=link_ping_timeout,
            inactive_timeout=inactive_timeout,
            session_timeout=session_timeout,
            allowed_devices=allowed_devices,
            max_clients=max_clients,
            max_devices=max_devices,
            replica_count=replica_count,
            vxlan=vxlan,
            dns_mapping=dns_mapping,
            debug=debug,
            pre_connect_msg=pre_connect_msg,
            mss_fix=mss_fix,
        )
        svr.add_host(settings.local.host_id)
    else:
        svr = server.get_by_id(server_id)

        if name_def:
            svr.name = name
        if network_def:
            svr.network = network
        if network_wg_def:
            svr.network_wg = network_wg
        if groups_def:
            svr.groups = groups
        if network_start_def:
            svr.network_start = network_start
        if network_end_def:
            svr.network_end = network_end
        if restrict_routes_def:
            svr.restrict_routes = restrict_routes
        if wg_def:
            svr.wg = wg
        if ipv6_def:
            svr.ipv6 = ipv6
        if ipv6_firewall_def:
            svr.ipv6_firewall = ipv6_firewall
        if network_mode_def:
            svr.network_mode = network_mode
        if bind_address_def:
            svr.bind_address = bind_address
        if port_def:
            svr.port = port
        if port_wg_def:
            svr.port_wg = port_wg
        if protocol_def:
            svr.protocol = protocol
        if dh_param_bits_def and svr.dh_param_bits != dh_param_bits:
            svr.dh_param_bits = dh_param_bits
            svr.generate_dh_param()
        if multi_device_def:
            svr.multi_device = multi_device
        if dns_servers_def:
            svr.dns_servers = dns_servers
        if search_domain_def:
            svr.search_domain = search_domain
        if otp_auth_def:
            svr.otp_auth = otp_auth
        if cipher_def:
            svr.cipher = cipher
        if hash_def:
            svr.hash = hash
        if block_outside_dns_def:
            svr.block_outside_dns = block_outside_dns
        if jumbo_frames_def:
            svr.jumbo_frames = jumbo_frames
        if lzo_compression_def:
            svr.lzo_compression = lzo_compression
        if inter_client_def:
            svr.inter_client = inter_client
        if ping_interval_def:
            svr.ping_interval = ping_interval
        if ping_timeout_def:
            svr.ping_timeout = ping_timeout
        if link_ping_interval_def:
            svr.link_ping_interval = link_ping_interval
        if link_ping_timeout_def:
            svr.link_ping_timeout = link_ping_timeout
        if inactive_timeout_def:
            svr.inactive_timeout = inactive_timeout
        if session_timeout_def:
            svr.session_timeout = session_timeout
        if allowed_devices_def:
            svr.allowed_devices = allowed_devices
        if max_clients_def:
            svr.max_clients = max_clients
        if max_devices_def:
            svr.max_devices = max_devices
        if replica_count_def:
            svr.replica_count = replica_count
        if vxlan_def:
            svr.vxlan = vxlan
        if dns_mapping_def:
            svr.dns_mapping = dns_mapping
        if debug_def:
            svr.debug = debug
        if pre_connect_msg_def:
            svr.pre_connect_msg = pre_connect_msg
        if mss_fix_def:
            svr.mss_fix = mss_fix

        changed = svr.changed

    svr.generate_auth_key()

    err, err_msg = svr.validate_conf()
    if err:
        return utils.jsonify({
            'error': err,
            'error_msg': err_msg,
        }, 400)

    svr.commit(changed)

    if not server_id:
        logger.LogEntry(message='Created server "%s".' % svr.name)

    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=svr.id)
    for org in svr.iter_orgs():
        event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify(svr.dict())

@app.app.route('/server/<server_id>', methods=['DELETE'])
@auth.session_auth
def server_delete(server_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id, fields=(
        '_id', 'name', 'organizations', 'links'))

    try:
        link_ids = svr.remove()
    except ServerLinkOnlineError:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_UNLINK_SERVER_MSG,
        }, 400)

    logger.LogEntry(message='Deleted server "%s".' % svr.name)

    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_LINKS_UPDATED, resource_id=server_id)
    for link_id in link_ids:
        event.Event(type=SERVER_LINKS_UPDATED, resource_id=link_id)

    for org in svr.iter_orgs():
        event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify({})

@app.app.route('/server/<server_id>/organization', methods=['GET'])
@auth.session_auth
def server_org_get(server_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    orgs = []
    svr = server.get_by_id(server_id, fields=('_id', 'organizations'))
    for org_doc in svr.get_org_fields(fields=('_id', 'name')):
        org_doc['id'] = org_doc.pop('_id')
        org_doc['server'] = svr.id
        orgs.append(org_doc)

    if settings.app.demo_mode:
        utils.demo_set_cache(orgs)
    return utils.jsonify(orgs)

@app.app.route('/server/<server_id>/organization/<org_id>', methods=['PUT'])
@auth.session_auth
def server_org_put(server_id, org_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id,
        fields=('_id', 'wg', 'status', 'network', 'network_wg',
        'network_start', 'network_end', 'organizations', 'routes', 'ipv6'))
    org = organization.get_by_id(org_id, fields=('_id', 'name'))
    if svr.status == ONLINE:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_ATTACH_ORG_MSG,
        }, 400)
    svr.add_org(org)
    svr.commit(svr.changed)
    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=svr.id)
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
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id,
        fields=('_id', 'wg', 'status', 'network', 'network_wg',
            'network_start', 'network_end', 'primary_organization',
            'primary_user', 'organizations', 'routes', 'ipv6'))
    org = organization.get_by_id(org_id, fields=('_id'))

    if svr.status == ONLINE:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_DETACH_ORG_MSG,
        }, 400)

    svr.remove_org(org)
    svr.commit(svr.changed)

    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=svr.id)
    event.Event(type=SERVER_ORGS_UPDATED, resource_id=svr.id)
    event.Event(type=USERS_UPDATED, resource_id=org.id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/route', methods=['GET'])
@auth.session_auth
def server_route_get(server_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    svr = server.get_by_id(server_id, fields=('_id', 'wg', 'network',
        'network_wg', 'links', 'network_start', 'network_end', 'routes',
        'organizations', 'ipv6'))

    resp = svr.get_routes(include_server_links=True, include_hidden=True)
    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)

@app.app.route('/server/<server_id>/route', methods=['POST'])
@auth.session_auth
def server_route_post(server_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id)
    route_network = flask.request.json['network']
    comment = flask.request.json.get('comment') or None
    metric = flask.request.json.get('metric') or None
    nat_route = True if flask.request.json.get('nat') else False
    nat_interface = flask.request.json.get('nat_interface') or None
    nat_netmap = flask.request.json.get('nat_netmap') or None
    advertise = True if flask.request.json.get('advertise') else False
    net_gateway = True if flask.request.json.get('net_gateway') else False

    try:
        route = svr.upsert_route(route_network, nat_route, nat_interface,
            nat_netmap, advertise, None, None, net_gateway, comment, metric)
    except ServerOnlineError:
        return utils.jsonify({
            'error': SERVER_ROUTE_ONLINE,
            'error_msg': SERVER_ROUTE_ONLINE_MSG,
        }, 400)
    except NetworkInvalid:
        return utils.jsonify({
            'error': SERVER_ROUTE_INVALID,
            'error_msg': SERVER_ROUTE_INVALID_MSG,
        }, 400)
    except ServerRouteNatVirtual:
        return utils.jsonify({
            'error': SERVER_ROUTE_VIRTUAL_NAT,
            'error_msg': SERVER_ROUTE_VIRTUAL_NAT_MSG,
        }, 400)
    except ServerRouteNatServerLink:
        return utils.jsonify({
            'error': SERVER_ROUTE_SERVER_LINK_NAT,
            'error_msg': SERVER_ROUTE_SERVER_LINK_NAT_MSG,
        }, 400)
    except ServerRouteGatewayNetworkLink:
        return utils.jsonify({
            'error': SERVER_ROUTE_NETWORK_LINK_GATEWAY,
            'error_msg': SERVER_ROUTE_NETWORK_LINK_GATEWAY_MSG,
        }, 400)
    except ServerRouteNatNetGateway:
        return utils.jsonify({
            'error': SERVER_ROUTE_NET_GATEWAY_NAT,
            'error_msg': SERVER_ROUTE_NET_GATEWAY_NAT_MSG,
        }, 400)
    except ServerRouteNonNatNetmap:
        return utils.jsonify({
            'error': SERVER_ROUTE_NON_NAT_NETMAP,
            'error_msg': SERVER_ROUTE_NON_NAT_NETMAP_MSG,
        }, 400)

    err, err_msg = svr.validate_conf()
    if err:
        return utils.jsonify({
            'error': err,
            'error_msg': err_msg,
        }, 400)

    svr.commit('routes')

    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=svr.id)
    for svr_link in svr.links:
        event.Event(type=SERVER_ROUTES_UPDATED,
            resource_id=svr_link['server_id'])

    return utils.jsonify(route)

@app.app.route('/server/<server_id>/routes', methods=['POST'])
@auth.session_auth
def server_routes_post(server_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id)

    for route_data in flask.request.json:
        route_network = route_data['network']
        comment = route_data.get('comment') or None
        metric = route_data.get('metric') or None
        nat_route = True if route_data.get('nat') else False
        nat_interface = route_data.get('nat_interface') or None
        nat_netmap = route_data.get('nat_netmap') or None
        advertise = True if route_data.get('advertise') else False
        net_gateway = True if route_data.get('net_gateway') else False

        try:
            route = svr.upsert_route(route_network, nat_route, nat_interface,
                nat_netmap, advertise, None, None, net_gateway, comment,
                metric)
        except ServerOnlineError:
            return utils.jsonify({
                'error': SERVER_ROUTE_ONLINE,
                'error_msg': SERVER_ROUTE_ONLINE_MSG,
            }, 400)
        except NetworkInvalid:
            return utils.jsonify({
                'error': SERVER_ROUTE_INVALID,
                'error_msg': SERVER_ROUTE_INVALID_MSG,
            }, 400)
        except ServerRouteNatVirtual:
            return utils.jsonify({
                'error': SERVER_ROUTE_VIRTUAL_NAT,
                'error_msg': SERVER_ROUTE_VIRTUAL_NAT_MSG,
            }, 400)
        except ServerRouteNatServerLink:
            return utils.jsonify({
                'error': SERVER_ROUTE_SERVER_LINK_NAT,
                'error_msg': SERVER_ROUTE_SERVER_LINK_NAT_MSG,
            }, 400)
        except ServerRouteGatewayNetworkLink:
            return utils.jsonify({
                'error': SERVER_ROUTE_NETWORK_LINK_GATEWAY,
                'error_msg': SERVER_ROUTE_NETWORK_LINK_GATEWAY_MSG,
            }, 400)
        except ServerRouteNatNetGateway:
            return utils.jsonify({
                'error': SERVER_ROUTE_NET_GATEWAY_NAT,
                'error_msg': SERVER_ROUTE_NET_GATEWAY_NAT_MSG,
            }, 400)
        except ServerRouteNonNatNetmap:
            return utils.jsonify({
                'error': SERVER_ROUTE_NON_NAT_NETMAP,
                'error_msg': SERVER_ROUTE_NON_NAT_NETMAP_MSG,
            }, 400)

    err, err_msg = svr.validate_conf()
    if err:
        return utils.jsonify({
            'error': err,
            'error_msg': err_msg,
        }, 400)

    svr.commit('routes')

    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=svr.id)
    for svr_link in svr.links:
        event.Event(type=SERVER_ROUTES_UPDATED,
            resource_id=svr_link['server_id'])

    return utils.jsonify(route)

@app.app.route('/server/<server_id>/route/<route_network>', methods=['PUT'])
@auth.session_auth
def server_route_put(server_id, route_network):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id)
    route_network = bytes.fromhex(route_network).decode()
    comment = flask.request.json.get('comment') or None
    metric = flask.request.json.get('metric') or None
    nat_route = True if flask.request.json.get('nat') else False
    nat_interface = flask.request.json.get('nat_interface') or None
    nat_netmap = flask.request.json.get('nat_netmap') or None
    advertise = True if flask.request.json.get('advertise') else False
    net_gateway = True if flask.request.json.get('net_gateway') else False

    try:
        route = svr.upsert_route(route_network, nat_route, nat_interface,
            nat_netmap, advertise, None, None, net_gateway, comment, metric)
    except ServerOnlineError:
        return utils.jsonify({
            'error': SERVER_ROUTE_ONLINE,
            'error_msg': SERVER_ROUTE_ONLINE_MSG,
        }, 400)
    except NetworkInvalid:
        return utils.jsonify({
            'error': SERVER_ROUTE_INVALID,
            'error_msg': SERVER_ROUTE_INVALID_MSG,
        }, 400)
    except ServerRouteNatVirtual:
        return utils.jsonify({
            'error': SERVER_ROUTE_VIRTUAL_NAT,
            'error_msg': SERVER_ROUTE_VIRTUAL_NAT_MSG,
        }, 400)
    except ServerRouteNatServerLink:
        return utils.jsonify({
            'error': SERVER_ROUTE_SERVER_LINK_NAT,
            'error_msg': SERVER_ROUTE_SERVER_LINK_NAT_MSG,
        }, 400)
    except ServerRouteGatewayNetworkLink:
        return utils.jsonify({
            'error': SERVER_ROUTE_NETWORK_LINK_GATEWAY,
            'error_msg': SERVER_ROUTE_NETWORK_LINK_GATEWAY_MSG,
        }, 400)
    except ServerRouteNatNetGateway:
        return utils.jsonify({
            'error': SERVER_ROUTE_NET_GATEWAY_NAT,
            'error_msg': SERVER_ROUTE_NET_GATEWAY_NAT_MSG,
        }, 400)
    except ServerRouteNonNatNetmap:
        return utils.jsonify({
            'error': SERVER_ROUTE_NON_NAT_NETMAP,
            'error_msg': SERVER_ROUTE_NON_NAT_NETMAP_MSG,
        }, 400)

    err, err_msg = svr.validate_conf()
    if err:
        return utils.jsonify({
            'error': err,
            'error_msg': err_msg,
        }, 400)

    svr.commit('routes')

    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=svr.id)
    for svr_link in svr.links:
        event.Event(type=SERVER_ROUTES_UPDATED,
            resource_id=svr_link['server_id'])

    return utils.jsonify(route)

@app.app.route('/server/<server_id>/route/<route_network>', methods=['DELETE'])
@auth.session_auth
def server_route_delete(server_id, route_network):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id)
    route_network = bytes.fromhex(route_network).decode()

    try:
        route = svr.remove_route(route_network)
    except ServerOnlineError:
        return utils.jsonify({
            'error': SERVER_ROUTE_ONLINE,
            'error_msg': SERVER_ROUTE_ONLINE_MSG,
        }, 400)

    err, err_msg = svr.validate_conf()
    if err:
        return utils.jsonify({
            'error': err,
            'error_msg': err_msg,
        }, 400)

    svr.commit('routes')

    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=svr.id)
    for svr_link in svr.links:
        event.Event(type=SERVER_ROUTES_UPDATED,
            resource_id=svr_link['server_id'])

    return utils.jsonify(route)

@app.app.route('/server/<server_id>/host', methods=['GET'])
@auth.session_auth
def server_host_get(server_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    hosts = []
    svr = server.get_by_id(server_id, fields=('_id', 'status',
        'replica_count', 'hosts', 'instances'))
    active_hosts = set([x['host_id'] for x in svr.instances])
    hosts_offline = svr.replica_count - len(active_hosts) > 0

    for hst in svr.iter_hosts(fields=('_id', 'name',
            'public_address', 'auto_public_address', 'auto_public_host',
            'public_address6', 'auto_public_address6', 'auto_public_host6')):
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
            'address6': hst.public_addr6,
        })

    if settings.app.demo_mode:
        utils.demo_set_cache(hosts)
    return utils.jsonify(hosts)

@app.app.route('/server/<server_id>/host/<host_id>', methods=['PUT'])
@auth.session_auth
def server_host_put(server_id, host_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id)
    if not svr:
        return flask.abort(404)
    hst = host.get_by_id(host_id, fields=('_id', 'name',
        'public_address', 'auto_public_address', 'auto_public_host',
        'public_address6', 'auto_public_address6', 'auto_public_host6'))
    if not svr:
        return flask.abort(404)

    try:
        svr.add_host(hst.id)
    except ServerLinkCommonHostError:
        return utils.jsonify({
            'error': SERVER_LINK_COMMON_HOST,
            'error_msg': SERVER_LINK_COMMON_HOST_MSG,
        }, 400)

    err, err_msg = svr.validate_conf(allow_online=True)
    if err:
        return utils.jsonify({
            'error': err,
            'error_msg': err_msg,
        }, 400)

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
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id, fields=(
        '_id', 'hosts', 'replica_count'))
    if not svr:
        return flask.abort(404)
    hst = host.get_by_id(host_id, fields=('_id', 'name'))
    if not hst:
        return flask.abort(404)

    svr.remove_host(hst.id)
    svr.commit('hosts')

    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/link', methods=['GET'])
@auth.session_auth
def server_link_get(server_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    links = []
    svr = server.get_by_id(server_id, fields=('_id', 'status', 'links',
        'replica_count', 'instances'))
    if not svr:
        return flask.abort(404)
    hosts_offline = svr.replica_count - len(svr.instances) > 0

    if svr.links:
        link_use_local = {}
        link_server_ids = []

        for link in svr.links:
            link_server_id = link['server_id']
            link_use_local[link_server_id] = link['use_local_address']
            link_server_ids.append(link_server_id)

        spec = {
            '_id': {'$in': link_server_ids},
        }
        for link_svr in server.iter_servers(spec=spec, fields=(
                '_id', 'status', 'name', 'replica_count', 'instances')):
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
                'use_local_address': link_use_local[link_svr.id],
            })

    if settings.app.demo_mode:
        utils.demo_set_cache(links)
    return utils.jsonify(links)

@app.app.route('/server/<server_id>/link/<link_server_id>', methods=['PUT'])
@auth.session_auth
def server_link_put(server_id, link_server_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    use_local_address = flask.request.json.get('use_local_address', False)

    err, err_msg = server.link_servers(
        server_id, link_server_id, use_local_address)
    if err:
        return utils.jsonify({
            'error': err,
            'error_msg': err_msg,
        }, 400)

    event.Event(type=SERVER_LINKS_UPDATED, resource_id=server_id)
    event.Event(type=SERVER_LINKS_UPDATED, resource_id=link_server_id)
    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=server_id)
    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=link_server_id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/link/<link_server_id>', methods=['DELETE'])
@auth.session_auth
def server_link_delete(server_id, link_server_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    try:
        server.unlink_servers(server_id, link_server_id)
    except ServerLinkOnlineError:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_UNLINK_SERVER_MSG,
        }, 400)

    event.Event(type=SERVER_LINKS_UPDATED, resource_id=server_id)
    event.Event(type=SERVER_LINKS_UPDATED, resource_id=link_server_id)
    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=server_id)
    event.Event(type=SERVER_ROUTES_UPDATED, resource_id=link_server_id)

    return utils.jsonify({})

@app.app.route('/server/<server_id>/operation/<operation>', methods=['PUT'])
@auth.session_auth
def server_operation_put(server_id, operation):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    svr = server.get_by_id(server_id, fields=server.operation_fields)

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
    for org in svr.iter_orgs():
        event.Event(type=USERS_UPDATED, resource_id=org.id)
    svr.send_link_events()

    return utils.jsonify(svr.dict())

@app.app.route('/server/<server_id>/output', methods=['GET'])
@auth.session_auth
def server_output_get(server_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    resp = {
        'id': server_id,
        'output': server.output_get(server_id),
    }
    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)

@app.app.route('/server/<server_id>/output', methods=['DELETE'])
@auth.session_auth
def server_output_delete(server_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    server.output_clear(server_id)
    return utils.jsonify({})

@app.app.route('/server/<server_id>/link_output', methods=['GET'])
@auth.session_auth
def server_link_output_get(server_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    resp = {
        'id': server_id,
        'output': server.output_link_get(server_id),
    }
    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)

@app.app.route('/server/<server_id>/link_output', methods=['DELETE'])
@auth.session_auth
def server_link_output_delete(server_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    server.output_link_clear(server_id)
    return utils.jsonify({})

@app.app.route('/server/<server_id>/bandwidth/<period>', methods=['GET'])
@auth.session_auth
def server_bandwidth_get(server_id, period):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    if settings.app.demo_mode:
        resp = server.bandwidth_random_get(server_id, period)
        utils.demo_set_cache(resp)
    else:
        resp = server.bandwidth_get(server_id, period)
    return utils.jsonify(resp)

@app.app.route('/server/vpcs', methods=['GET'])
@auth.session_auth
def server_vpcs_get():
    return utils.jsonify(utils.get_vpcs())
