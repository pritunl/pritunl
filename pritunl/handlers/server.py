from pritunl.constants import *
from pritunl.server import Server
from pritunl.organization import Organization
from event import Event
import pritunl.utils as utils
from pritunl import app_server
import flask

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
        server_orgs = server.get_orgs()
        users_count = 0
        for org in server_orgs:
            for user in org.get_users():
                if user.type != CERT_CLIENT:
                    continue
                users_count += 1

        name_id = '%s_%s' % (server.name, server.id)
        servers_sort.append(name_id)
        servers_dict[name_id] = {
            'id': server.id,
            'name': server.name,
            'status': 'online' if server.status else 'offline',
            'uptime': server.uptime,
            'users_online': len(server.get_clients()),
            'users_total': users_count,
            'network': server.network,
            'interface': server.interface,
            'port': server.port,
            'protocol': server.protocol,
            'local_network': server.local_network,
            'public_address': server.public_address,
            'otp_auth': True if server.otp_auth else False,
            'lzo_compression': server.lzo_compression,
            'debug': True if server.debug else False,
            'org_count': len(server_orgs),
        }

    for name_id in sorted(servers_sort):
        servers.append(servers_dict[name_id])

    return utils.jsonify(servers)

@app_server.app.route('/server', methods=['POST'])
@app_server.app.route('/server/<server_id>', methods=['PUT'])
@app_server.auth
def server_put_post(server_id=None):
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    network = flask.request.json['network']
    interface = flask.request.json['interface']
    port = flask.request.json['port']
    protocol = flask.request.json['protocol'].lower()
    local_network = flask.request.json['local_network']
    if local_network:
        local_network = local_network
    public_address = flask.request.json['public_address']
    public_address = ''.join(
        x for x in public_address if x.isalnum() or x == '.')
    debug = True if flask.request.json['debug'] else False
    otp_auth = True if flask.request.json['otp_auth'] else False
    lzo_compression = True if flask.request.json['lzo_compression'] else False

    # Network
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

    # Interface
    if interface[:3] != 'tun':
        return _interface_not_valid()

    try:
        interface_num = int(interface[3:])
    except ValueError:
        return _interface_not_valid()

    if interface_num > 64:
        return _interface_not_valid()

    interface = interface[:3] + str(interface_num)

    # Port
    try:
        port = int(port)
    except ValueError:
        return _port_not_valid()

    if port < 1 or port > 65535:
        return _port_not_valid()

    # Protocol
    if protocol not in ['udp', 'tcp']:
        return utils.jsonify({
            'error': PROTOCOL_NOT_VALID,
            'error_msg': PROTOCOL_NOT_VALID_MSG,
        }, 400)

    # Local network
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

    for server in Server.get_servers():
        if server.id == server_id:
            continue
        elif server.network == network:
            return utils.jsonify({
                'error': NETWORK_IN_USE,
                'error_msg': NETWORK_IN_USE_MSG,
            }, 400)
        elif server.interface == interface:
            return utils.jsonify({
                'error': INTERFACE_IN_USE,
                'error_msg': INTERFACE_IN_USE_MSG,
            }, 400)
        elif server.port == port and server.protocol == protocol:
            return utils.jsonify({
                'error': PORT_PROTOCOL_IN_USE,
                'error_msg': PORT_PROTOCOL_IN_USE_MSG,
            }, 400)

    if not server_id:
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
        server.name = name
        server.network = network
        server.interface = interface
        server.port = port
        server.protocol = protocol
        server.local_network = local_network
        server.public_address = public_address
        server.otp_auth = otp_auth
        server.lzo_compression = lzo_compression
        server.debug = debug
        server.commit()

    Event(type=USERS_UPDATED)

    return utils.jsonify({})

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
    server.add_org(org_id)
    return utils.jsonify({})

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
    return utils.jsonify({})

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
