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

import flask
import re
import random

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

@app.app.route('/server', methods=['GET'])
@app.app.route('/server/<server_id>', methods=['GET'])
@auth.session_auth
def server_get(server_id=None):
    if server_id:
        return utils.jsonify(server.get_server_dict(server_id))

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

            if subnet < 8 or subnet > 30:
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
                if rand_network not in network_used:
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
        if network in network_used:
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
            port=port,
            protocol=protocol,
            dh_param_bits=dh_param_bits,
            mode=mode,
            local_networks=local_networks,
            dns_servers=dns_servers,
            search_domain=search_domain,
            otp_auth=otp_auth,
            lzo_compression=lzo_compression,
            debug=debug,
        )
        svr.commit()
    else:
        svr = server.get_server(id=server_id)
        if svr.status:
            return utils.jsonify({
                'error': SERVER_NOT_OFFLINE,
                'error_msg': SERVER_NOT_OFFLINE_SETTINGS_MSG,
            }, 400)
        if name_def:
            svr.name = name
        if network_def:
            svr.network = network
        if port_def:
            svr.port = port
        if protocol_def:
            svr.protocol = protocol
        if dh_param_bits_def and svr.dh_param_bits != dh_param_bits:
            svr.dh_param_bits = dh_param_bits
            svr.generate_dh_param()
        if mode_def:
            svr.mode = mode
        if local_networks_def:
            svr.local_networks = local_networks
        if dns_servers_def:
            svr.dns_servers = dns_servers
        if search_domain_def:
            svr.search_domain = search_domain
        if otp_auth_def:
            svr.otp_auth = otp_auth
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
    svr = server.get_server(id=server_id, fields=['_id', 'organizations'])
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
    svr = server.get_server(id=server_id, fields=['_id', 'organizations'])
    for org_doc in svr.get_org_fields(fields=['_id', 'name']):
        org_doc['id'] = str(org_doc.pop('_id'))
        org_doc['server'] = svr.id
        orgs.append(org_doc)

    return utils.jsonify(orgs)

@app.app.route('/server/<server_id>/organization/<org_id>',
    methods=['PUT'])
@auth.session_auth
def server_org_put(server_id, org_id):
    svr = server.get_server(id=server_id,
        fields=['id', 'status', 'organizations'])
    org = organization.get_org(id=org_id, fields=['_id'])
    if svr.status:
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
    svr = server.get_server(id=server_id,
        fields=['_id', 'status', 'organizations'])
    org = organization.get_org(id=org_id, fields=['_id'])
    if svr.status:
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
    svr = server.get_server(id=server_id, fields=['_id', 'hosts', 'instances'])
    active_hosts = set([x['host_id'] for x in svr.instances])

    for hst in svr.iter_hosts(fields=['_id', 'name', 'public_addr']):
        hosts.append({
            'id': hst.id,
            'server': svr.id,
            'status': ONLINE if hst.id in active_hosts else OFFLINE,
            'name': hst.name,
            'public_address': hst.public_addr,
        })

    return utils.jsonify(hosts)

@app.app.route('/server/<server_id>/host/<host_id>', methods=['PUT'])
@auth.session_auth
def server_host_put(server_id, host_id):
    svr = server.get_server(id=server_id, fields=['_id', 'hosts'])
    hst = host.get_host(id=host_id, fields=['_id', 'name', 'public_addr'])
    svr.add_host(hst)
    svr.commit('hosts')
    event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)

    return utils.jsonify({
        'id': hst.id,
        'server': svr.id,
        'status': OFFLINE,
        'name': hst.name,
        'public_address': hst.public_addr,
    })

@app.app.route('/server/<server_id>/host/<host_id>', methods=['DELETE'])
@auth.session_auth
def server_host_delete(server_id, host_id):
    svr = server.get_server(id=server_id, fields=['_id', 'hosts'])
    hst = host.get_host(id=host_id, fields=['_id', 'name'])
    svr.remove_host(hst)
    svr.commit('hosts')
    event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)
    return utils.jsonify({})

@app.app.route('/server/<server_id>/<operation>', methods=['PUT'])
@auth.session_auth
def server_operation_put(server_id, operation):
    svr = server.get_server(id=server_id, fields=server.dict_fields + \
        ['hosts', 'organizations'])

    if operation == START:
        svr.start()
        logger.LogEntry(message='Started server "%s".' % svr.name)
    if operation == STOP:
        svr.stop()
        logger.LogEntry(message='Stopped server "%s".' % svr.name)
    elif operation == RESTART:
        svr.restart()
        logger.LogEntry(message='Restarted server "%s".' % svr.name)
    event.Event(type=SERVERS_UPDATED)
    event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)

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

@app.app.route('/server/<server_id>/tls_verify', methods=['POST'])
@auth.server_auth
def server_tls_verify_post(server_id):
    org_id = flask.request.json['org_id']
    user_id = flask.request.json['user_id']

    svr = server.get_server(server_id,
        fields=['_id', 'name', 'organizations'])
    if not svr:
        return utils.jsonify({
            'error': SERVER_INVALID,
            'error_msg': SERVER_INVALID_MSG,
        }, 401)
    org = svr.get_org(org_id, fields=['_id'])
    if not org:
        logger.LogEntry(message='User failed authentication, ' +
            'invalid organization "%s" on server "%s".' % (org_id, svr.name))
        return utils.jsonify({
            'error': ORG_INVALID,
            'error_msg': ORG_INVALID_MSG,
        }, 401)
    user = org.get_user(user_id, fields=['_id', 'name', 'disabled'])
    if not user:
        logger.LogEntry(message='User failed authentication, ' +
            'invalid user "%s" on server "%s".' % (user_id, svr.name))
        return utils.jsonify({
            'error': USER_INVALID,
            'error_msg': USER_INVALID_MSG,
        }, 401)
    if user.disabled:
        logger.LogEntry(message='User failed authentication, ' +
            'disabled user "%s" on server "%s".' % (user.name, svr.name))
        return utils.jsonify({
            'error': USER_INVALID,
            'error_msg': USER_INVALID_MSG,
        }, 401)

    return utils.jsonify({
        'authenticated': True,
    })

@app.app.route('/server/<server_id>/otp_verify', methods=['POST'])
@auth.server_auth
def server_otp_verify_post(server_id):
    org_id = flask.request.json['org_id']
    user_id = flask.request.json['user_id']
    otp_code = flask.request.json['otp_code']
    remote_ip = flask.request.json.get('remote_ip')

    svr = server.get_server(server_id,
        fields=['_id', 'name', 'organizations'])
    if not svr:
        return utils.jsonify({
            'error': SERVER_INVALID,
            'error_msg': SERVER_INVALID_MSG,
        }, 401)
    org = svr.get_org(org_id, fields=['_id'])
    if not org:
        logger.LogEntry(message='User failed authentication, ' +
            'invalid organization on server "%s".' % svr.name)
        return utils.jsonify({
            'error': ORG_INVALID,
            'error_msg': ORG_INVALID_MSG,
        }, 401)
    user = org.get_user(user_id, fields=['_id', 'name', 'type' ,'otp_secret'])
    if not user:
        logger.LogEntry(message='User failed authentication, ' +
            'invalid user on server "%s".' % svr.name)
        return utils.jsonify({
            'error': USER_INVALID,
            'error_msg': USER_INVALID_MSG,
        }, 401)
    if user.type == CERT_CLIENT and \
            not user.verify_otp_code(otp_code, remote_ip):
        logger.LogEntry(message='User failed two-step authentication "%s".' % (
            user.name))
        return utils.jsonify({
            'error': OTP_CODE_INVALID,
            'error_msg': OTP_CODE_INVALID_MSG,
        }, 401)

    return utils.jsonify({
        'authenticated': True,
    })

@app.app.route('/server/<server_id>/client_connect', methods=['POST'])
@auth.server_auth
def server_client_connect_post(server_id):
    org_id = flask.request.json['org_id']
    user_id = flask.request.json['user_id']

    svr = server.get_server(id=server_id,
        fields=['_id', 'name', 'links', 'organizations'])
    if not svr:
        return utils.jsonify({
            'error': SERVER_INVALID,
            'error_msg': SERVER_INVALID_MSG,
        }, 401)
    org = svr.get_org(org_id, fields=['_id'])
    if not org:
        return utils.jsonify({
            'error': ORG_INVALID,
            'error_msg': ORG_INVALID_MSG,
        }, 401)
    user = org.get_user(user_id, fields=['_id', 'name', 'disabled'])
    if not user:
        return utils.jsonify({
            'error': USER_INVALID,
            'error_msg': USER_INVALID_MSG,
        }, 401)

    client_conf = ''

    if user.id in svr.links.values():
        for link_svr_id, link_usr_id in svr.links.iteritems():
            if user.id == link_usr_id:
                link_svr = server.get_server(id=link_svr_id,
                    fields=['_id', 'network', 'local_networks'])
                client_conf += 'iroute %s %s\n' % utils.parse_network(
                    link_svr.network)
                for local_network in link_svr.local_networks:
                    push += 'iroute %s %s\n' % utils.parse_network(
                        local_network)

    local_ip_addr, remote_ip_addr = svr.get_ip_set(org.id, user_id)
    if local_ip_addr and remote_ip_addr:
        client_conf += 'ifconfig-push %s %s\n' % (
            local_ip_addr, remote_ip_addr)

    return utils.jsonify({
        'client_conf': client_conf,
    })

@app.app.route('/server/<server_id>/client_disconnect',
    methods=['POST'])
@auth.server_auth
def server_client_disconnect_post(server_id):
    org_id = flask.request.json['org_id']
    user_id = flask.request.json['user_id']

    svr = server.get_server(id=server_id, fields=['_id', 'organizations'])
    if not svr:
        return utils.jsonify({
            'error': SERVER_INVALID,
            'error_msg': SERVER_INVALID_MSG,
        }, 401)
    org = svr.get_org(org_id, fields=['_id'])
    if not org:
        return utils.jsonify({
            'error': ORG_INVALID,
            'error_msg': ORG_INVALID_MSG,
        }, 401)
    user = org.get_user(user_id, fields=['_id'])
    if not user:
        return utils.jsonify({
            'error': USER_INVALID,
            'error_msg': USER_INVALID_MSG,
        }, 401)

    return utils.jsonify({})
