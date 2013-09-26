from pritunl.constants import *
from pritunl.server import Server
from pritunl.organization import Organization
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
            'status': 'online',
            'uptime': 88573,
            'users_online': 16,
            'users_total': 32,
            'network': server.network,
            'interface': server.interface,
            'port': server.port,
            'protocol': server.protocol,
            'local_network': server.local_network,
            'public_address': server.public_address,
        }

    for name_id in sorted(servers_sort):
        servers.append(servers_dict[name_id])

    return utils.jsonify(servers)

@app_server.app.route('/server', methods=['POST'])
@app_server.app.route('/server/<server_id>', methods=['PUT'])
def server_put_post(server_id=None):
    name = flask.request.json['name'].encode()
    network = flask.request.json['network'].encode()
    interface = flask.request.json['interface'].encode()
    port = flask.request.json['port'].encode()
    protocol = flask.request.json['protocol'].encode().lower()
    local_network = flask.request.json['local_network']
    if local_network:
        local_network = local_network.encode()
    public_address = flask.request.json['public_address'].encode()

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

    if not server_id:
        ovpn_server = Server(
            name=name,
            network=network,
            interface=interface,
            port=port,
            protocol=protocol,
            local_network=local_network,
            public_address=public_address,
        )
    else:
        ovpn_server = Server(id=server_id)
        ovpn_server.name = name
        ovpn_server.network = network
        ovpn_server.interface = interface
        ovpn_server.port = port
        ovpn_server.protocol = protocol
        ovpn_server.local_network = local_network
        ovpn_server.public_address = public_address
        ovpn_server.commit()

    return utils.jsonify({})

@app_server.app.route('/server/<server_id>', methods=['DELETE'])
def server_delete(server_id):
    ovpn_server = Server(server_id)
    ovpn_server.remove()
    return utils.jsonify({})

@app_server.app.route('/server/<server_id>/organization', methods=['GET'])
def server_org_get(server_id):
    orgs = []
    orgs_dict = {}
    orgs_sort = []
    ovpn_server = Server(server_id)

    for org_id in ovpn_server.organizations:
        org = Organization(org_id)
        name_id = '%s_%s' % (org.name, org.id)
        orgs_sort.append(name_id)
        orgs_dict[name_id] = {
            'id': org.id,
            'server': ovpn_server.id,
            'name': org.name,
        }

    for name_id in sorted(orgs_sort):
        orgs.append(orgs_dict[name_id])

    return utils.jsonify(orgs)

@app_server.app.route('/server/<server_id>/organization/<org_id>',
    methods=['PUT'])
def server_org_put(server_id, org_id):
    ovpn_server = Server(server_id)
    ovpn_server.add_org(org_id)
    return utils.jsonify({})

@app_server.app.route('/server/<server_id>/organization/<org_id>',
    methods=['DELETE'])
def server_org_delete(server_id, org_id):
    ovpn_server = Server(server_id)
    ovpn_server.remove_org(org_id)
    return utils.jsonify({})

@app_server.app.route('/server/<server_id>/<operation>', methods=['PUT'])
def server_operation_put(server_id, operation):
    return utils.jsonify({})
