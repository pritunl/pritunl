from pritunl.constants import *
from pritunl.server import Server
from pritunl.organization import Organization
from event import Event
import pritunl.utils as utils
from pritunl import app_server
import flask
import random

def _network_not_valid():
    return utils.jsonify({
        'error': NETWORK_NOT_VALID,
        'error_msg': NETWORK_NOT_VALID_MSG,
    }, 400)

def _interface_not_valid():
        return utils.jsonify({
            'error': INTERFACE_NOT_VALID,
            'error_msg': INTERFACE_NOT_VALID_MSG,
        }, 400)

def _port_not_valid():
        return utils.jsonify({
            'error': PORT_NOT_VALID,
            'error_msg': PORT_NOT_VALID_MSG,
        }, 400)

def _local_network_not_valid():
    return utils.jsonify({
        'error': LOCAL_NETWORK_NOT_VALID,
        'error_msg': LOCAL_NETWORK_NOT_VALID_MSG,
    }, 400)

@app_server.app.route('/server', methods=['GET'])
@app_server.auth
def server_get():
    servers = []
    servers_dict = {}
    servers_sort = []

    for server in Server.get_servers():
        name_id = '%s_%s' % (server.name, server.id)
        servers_sort.append(name_id)
        servers_dict[name_id] = {
            'id': server.id,
            'name': server.name,
            'status': server.status,
            'uptime': server.uptime,
            'users_online': len(server.get_clients()),
            'user_count': server.user_count,
            'network': server.network,
            'interface': server.interface,
            'port': server.port,
            'protocol': server.protocol,
            'local_network': server.local_network,
            'public_address': server.public_address,
            'otp_auth': True if server.otp_auth else False,
            'lzo_compression': server.lzo_compression,
            'debug': True if server.debug else False,
            'org_count': server.org_count,
        }

    for name_id in sorted(servers_sort):
        servers.append(servers_dict[name_id])

    return utils.jsonify(servers)

@app_server.app.route('/server', methods=['POST'])
@app_server.app.route('/server/<server_id>', methods=['PUT'])
@app_server.auth
def server_put_post(server_id=None):
    network_used = set()
    interface_used = set()
    port_used = set()
    for server in Server.get_servers():
        if server.id == server_id:
            continue
        network_used.add(server.network)
        interface_used.add(server.interface)
        port_used.add('%s%s' % (server.port, server.protocol))

    name = None
    name_def = False
    if 'name' in flask.request.json:
        name_def = True
        name = flask.request.json['name']
        name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)

    network = None
    network_def = False
    if 'network' in flask.request.json:
        network_def = True
        network = flask.request.json['network']

        network_split = network.split('/')
        if len(network_split) != 2:
            return _network_not_valid()

        address = network_split[0].split('.')
        if len(address) != 4:
            return _network_not_valid()
        for i, value in enumerate(address):
            try:
                address[i] = int(value)
            except ValueError:
                return _network_not_valid()
        if address[0] != 10:
            return _network_not_valid()

        if address[1] > 255 or address[1] < 0 or \
                address[2] > 255 or address[2] < 0:
            return _network_not_valid()

        if address[3] != 0:
            return _network_not_valid()

        try:
            subnet = int(network_split[1])
        except ValueError:
            return _network_not_valid()

        if subnet < 8 or subnet > 24:
            return _network_not_valid()

    interface = None
    interface_def = False
    if 'interface' in flask.request.json:
        interface_def = True
        interface = flask.request.json['interface']

        if interface[:3] != 'tun':
            return _interface_not_valid()

        try:
            interface_num = int(interface[3:])
        except ValueError:
            return _interface_not_valid()

        if interface_num > 64:
            return _interface_not_valid()

        interface = interface[:3] + str(interface_num)

    protocol = 'udp'
    protocol_def = False
    if 'protocol' in flask.request.json:
        protocol_def = True
        protocol = flask.request.json['protocol'].lower()

        if protocol not in {'udp', 'tcp'}:
            return utils.jsonify({
                'error': PROTOCOL_NOT_VALID,
                'error_msg': PROTOCOL_NOT_VALID_MSG,
            }, 400)

    port = None
    port_def = False
    if 'port' in flask.request.json:
        port_def = True
        port = flask.request.json['port']

        try:
            port = int(port)
        except ValueError:
            return _port_not_valid()

        if port < 1 or port > 65535:
            return _port_not_valid()

    local_network = None
    local_network_def = False
    if 'local_network' in flask.request.json:
        local_network_def = True
        local_network = flask.request.json['local_network']

        if local_network:
            local_network_split = local_network.split('/')
            if len(local_network_split) != 2:
                return _local_network_not_valid()

            address = local_network_split[0].split('.')
            if len(address) != 4:
                return _local_network_not_valid()
            for i, value in enumerate(address):
                try:
                    address[i] = int(value)
                except ValueError:
                    return _local_network_not_valid()
            if address[0] > 255 or address[0] < 0 or \
                    address[1] > 255 or address[1] < 0 or \
                    address[2] > 255 or address[2] < 0 or \
                    address[3] > 254 or address[3] < 0:
                return _local_network_not_valid()

            try:
                subnet = int(local_network_split[1])
            except ValueError:
                return _local_network_not_valid()

            if subnet < 8 or subnet > 30:
                return _local_network_not_valid()

    public_address = None
    public_address_def = False
    if 'public_address' in flask.request.json:
        public_address_def = True
        public_address = flask.request.json['public_address']
        public_address = ''.join(
            x for x in public_address if x.isalnum() or x == '.')

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

    if not server_id:
        if not name_def:
            return utils.jsonify({
                'error': MISSING_PARAMS,
                'error_msg': MISSING_PARAMS_MSG,
            }, 400)

        if not network_def:
            for i in xrange(5000):
                rand_network = '10.%s.%s.0/24' % (
                    random.randint(15,250), random.randint(15,250))
                if rand_network not in network_used:
                    network = rand_network
                    break
            if not network:
                return utils.jsonify({
                    'error': NETWORK_IN_USE,
                    'error_msg': NETWORK_IN_USE_MSG,
                }, 400)

        if not interface_def:
            for i in xrange(64):
                rand_interface = 'tun%s' % i
                if rand_interface not in interface_used:
                    interface = rand_interface
                    break
            if not interface:
                return utils.jsonify({
                    'error': INTERFACE_IN_USE,
                    'error_msg': INTERFACE_IN_USE_MSG,
                }, 400)

        if not port_def:
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

        server = Server(
            name=name,
            network=network,
            interface=interface,
            port=port,
            protocol=protocol,
            local_network=local_network,
            public_address=public_address,
            otp_auth=otp_auth,
            lzo_compression=lzo_compression,
            debug=debug,
        )
    else:
        server = Server(id=server_id)
        if server.status:
            return utils.jsonify({
                'error': SERVER_NOT_OFFLINE,
                'error_msg': SERVER_NOT_OFFLINE_SETTINGS_MSG,
            }, 400)
        if name_def:
            server.name = name
        if network_def:
            if network in network_used:
                return utils.jsonify({
                    'error': NETWORK_IN_USE,
                    'error_msg': NETWORK_IN_USE_MSG,
                }, 400)
            server.network = network
        if interface_def:
            if interface in interface_used:
                return utils.jsonify({
                    'error': INTERFACE_IN_USE,
                    'error_msg': INTERFACE_IN_USE_MSG,
                }, 400)
            server.interface = interface
        if port_def:
            if '%s%s' % (port, protocol) in port_used:
                return utils.jsonify({
                    'error': PORT_PROTOCOL_IN_USE,
                    'error_msg': PORT_PROTOCOL_IN_USE_MSG,
                }, 400)
            server.port = port
        if protocol_def:
            server.protocol = protocol
        if local_network_def:
            server.local_network = local_network
        if public_address_def:
            server.public_address = public_address
        if otp_auth_def:
            server.otp_auth = otp_auth
        if lzo_compression_def:
            server.lzo_compression = lzo_compression
        if debug_def:
            server.debug = debug
        server.commit()

    Event(type=USERS_UPDATED)

    return utils.jsonify({
        'id': server.id,
        'name': server.name,
        'status': server.status,
        'uptime': server.uptime,
        'users_online': len(server.get_clients()),
        'user_count': server.user_count,
        'network': server.network,
        'interface': server.interface,
        'port': server.port,
        'protocol': server.protocol,
        'local_network': server.local_network,
        'public_address': server.public_address,
        'otp_auth': True if server.otp_auth else False,
        'lzo_compression': server.lzo_compression,
        'debug': True if server.debug else False,
        'org_count': server.org_count,
    })

@app_server.app.route('/server/<server_id>', methods=['DELETE'])
@app_server.auth
def server_delete(server_id):
    server = Server(server_id)
    server.remove()
    return utils.jsonify({})

@app_server.app.route('/server/<server_id>/organization', methods=['GET'])
@app_server.auth
def server_org_get(server_id):
    orgs = []
    orgs_dict = {}
    orgs_sort = []
    server = Server(server_id)

    for org in server.get_orgs():
        name_id = '%s_%s' % (org.name, org.id)
        orgs_sort.append(name_id)
        orgs_dict[name_id] = {
            'id': org.id,
            'server': server.id,
            'name': org.name,
        }

    for name_id in sorted(orgs_sort):
        orgs.append(orgs_dict[name_id])

    return utils.jsonify(orgs)

@app_server.app.route('/server/<server_id>/organization/<org_id>',
    methods=['PUT'])
@app_server.auth
def server_org_put(server_id, org_id):
    server = Server(server_id)
    if server.status:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_ATTACH_ORG_MSG,
        }, 400)
    org = server.add_org(org_id)
    return utils.jsonify({
        'id': org.id,
        'server': server.id,
        'name': org.name,
    })

@app_server.app.route('/server/<server_id>/organization/<org_id>',
    methods=['DELETE'])
@app_server.auth
def server_org_delete(server_id, org_id):
    server = Server(server_id)
    if server.status:
        return utils.jsonify({
            'error': SERVER_NOT_OFFLINE,
            'error_msg': SERVER_NOT_OFFLINE_DETACH_ORG_MSG,
        }, 400)
    server.remove_org(org_id)
    return utils.jsonify({})

@app_server.app.route('/server/<server_id>/<operation>', methods=['PUT'])
@app_server.auth
def server_operation_put(server_id, operation):
    server = Server(server_id)
    if operation == START:
        server.start()
    if operation == STOP:
        server.stop()
    elif operation == RESTART:
        server.restart()
    return utils.jsonify({
        'id': server.id,
        'name': server.name,
        'status': server.status,
        'uptime': server.uptime,
        'users_online': len(server.get_clients()),
        'user_count': server.user_count,
        'network': server.network,
        'interface': server.interface,
        'port': server.port,
        'protocol': server.protocol,
        'local_network': server.local_network,
        'public_address': server.public_address,
        'otp_auth': True if server.otp_auth else False,
        'lzo_compression': server.lzo_compression,
        'debug': True if server.debug else False,
        'org_count': server.org_count,
    })

@app_server.app.route('/server/<server_id>/output', methods=['GET'])
@app_server.auth
def server_output_get(server_id):
    server = Server(server_id)
    return utils.jsonify({
        'id': server.id,
        'output': server.get_output(),
    })

@app_server.app.route('/server/<server_id>/output', methods=['DELETE'])
@app_server.auth
def server_output_delete(server_id):
    server = Server(server_id)
    server.clear_output()
    return utils.jsonify({})
