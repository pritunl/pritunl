from pritunl.utils.misc import check_output_logged

from pritunl.constants import *
from pritunl import ipaddress

import flask
import re
import socket
import struct
import fcntl

_tun_interfaces = set(['tun%s' % _x for _x in xrange(100)])
_tap_interfaces = set(['tap%s' % _x for _x in xrange(100)])
_sock = None
_sockfd = None

def interface_acquire(interface_type):
    if interface_type == 'tun':
        return _tun_interfaces.pop()
    elif interface_type == 'tap':
        return _tap_interfaces.pop()
    else:
        raise ValueError('Unknown interface type %s' % interface_type)

def interface_release(interface_type, interface):
    if interface_type == 'tun':
        _tun_interfaces.add(interface)
    elif interface_type == 'tap':
        _tap_interfaces.add(interface)
    else:
        raise ValueError('Unknown interface type %s' % interface_type)

def get_remote_addr():
    return flask.request.remote_addr

def get_interface_address(interface):
    global _sock
    global _sockfd

    if _sock is None:
        try:
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _sockfd = _sock.fileno()
        except:
            _sock = False
            _sockfd = False

    if not _sock:
        return

    ifreq = struct.pack('16sH14s', interface, socket.AF_INET, '\x00' * 14)
    try:
        res = fcntl.ioctl(_sockfd, 0x8915, ifreq)
    except:
        return
    return socket.inet_ntoa(struct.unpack('16sH2x4s8x', res)[2])

def ip_to_long(ip_str):
    ip = ip_str.split('.')
    ip.reverse()
    while len(ip) < 4:
        ip.insert(1, '0')
    return sum(long(byte) << 8 * i for i, byte in enumerate(ip))

def long_to_ip(ip_num):
    return '.'.join(map(str, [
        (ip_num >> 24) & 0xff,
        (ip_num >> 16) & 0xff,
        (ip_num >> 8) & 0xff,
        ip_num & 0xff,
    ]))

def subnet_to_cidr(subnet):
    count = 0
    while ~ip_to_long(subnet) & pow(2, count):
        count += 1
    return 32 - count

def network_addr(ip, subnet):
    return '%s/%s' % (long_to_ip(ip_to_long(ip) & ip_to_long(subnet)),
        subnet_to_cidr(subnet))

def parse_network(network):
    address = ipaddress.IPNetwork(network)
    return str(address.ip), str(address.netmask)

def get_network_gateway(network):
    return str(ipaddress.IPNetwork(network).iterhosts().next())

def get_local_networks():
    addresses = []
    output = check_output_logged(['ifconfig'])

    for interface in output.split('\n\n'):
        interface_name = re.findall(r'[a-z0-9]+', interface, re.IGNORECASE)
        if not interface_name:
            continue
        interface_name = interface_name[0]

        if re.search(r'tun[0-9]+', interface_name) or interface_name == 'lo':
            continue

        addr = re.findall(r'inet.{0,10}' + IP_REGEX, interface, re.IGNORECASE)
        if not addr:
            continue

        addr = re.findall(IP_REGEX, addr[0], re.IGNORECASE)
        if not addr:
            continue

        mask = re.findall(r'mask.{0,10}' + IP_REGEX, interface, re.IGNORECASE)
        if not mask:
            continue

        mask = re.findall(IP_REGEX, mask[0], re.IGNORECASE)
        if not mask:
            continue

        addr = addr[0]
        mask = mask[0]
        if addr.split('.')[0] == '127':
            continue

        addresses.append(network_addr(addr, mask))

    return addresses

def get_routes():
    routes_output = check_output_logged(['route', '-n'])

    routes = {}
    for line in routes_output.splitlines():
        line_split = line.split()
        if len(line_split) < 8 or not re.match(IP_REGEX, line_split[0]):
            continue
        routes[line_split[0]] = line_split[7]

    return routes

def get_gateway():
    routes_output = check_output_logged(['route', '-n'])

    for line in routes_output.splitlines():
        line_split = line.split()
        if len(line_split) < 8 or not re.match(IP_REGEX, line_split[0]) or \
                not re.match(IP_REGEX, line_split[1]):
            continue

        if line_split[0] == '0.0.0.0':
            return (line_split[7], line_split[1])

def get_interfaces():
    gateway = get_gateway()
    if not gateway:
        from pritunl import logger
        logger.error('Failed to find gateway address', 'utils')
    gateway_inf, gateway_addr = gateway

    output = check_output_logged(['ifconfig'])
    interfaces = {}

    for interface in output.split('\n\n'):
        data = {}

        interface_name = re.findall(r'[a-z0-9]+', interface, re.IGNORECASE)
        if not interface_name:
            continue
        interface_name = interface_name[0]
        data['interface'] = interface_name

        addr = re.findall(r'inet.{0,10}' + IP_REGEX, interface, re.IGNORECASE)
        if not addr:
            continue
        addr = re.findall(IP_REGEX, addr[0], re.IGNORECASE)
        if not addr:
            continue
        data['address'] = addr[0]

        netmask = re.findall(r'mask.{0,10}' + IP_REGEX,
            interface, re.IGNORECASE)
        if not netmask:
            continue
        netmask = re.findall(IP_REGEX, netmask[0], re.IGNORECASE)
        if not netmask:
            continue
        data['netmask'] = netmask[0]

        broadcast = re.findall(r'broadcast.{0,10}' + IP_REGEX,
            interface, re.IGNORECASE)
        if not broadcast:
            broadcast = re.findall(r'bcast.{0,10}' + IP_REGEX,
                interface, re.IGNORECASE)
        if not broadcast:
            continue
        broadcast = re.findall(IP_REGEX, broadcast[0], re.IGNORECASE)
        if not broadcast:
            continue
        data['broadcast'] = broadcast[0]

        if data['interface'] == gateway_inf:
            data['gateway'] = gateway_addr
        else:
            data['gateway'] = None

        interfaces[interface_name] = data

    return interfaces

def find_interface(network):
    network = ipaddress.IPNetwork(network)

    for interface, data in get_interfaces().items():
        try:
            address = ipaddress.IPAddress(data['address'])
        except ValueError:
            continue

        if address in network and data['netmask'] == str(network.netmask):
            return data

def net4to6(prefix, net):
    net, cidr = net.split('/')
    nets = net.split('.')
    cidr = int(cidr)

    net_num = int(nets[0]) * 256**3 + int(nets[1]) * 256**2 + \
        int(nets[2]) * 256**1 + int(nets[3]) * 256**0
    net_hex = hex(net_num + cidr * 256**4)

    net6 = prefix + ':' + net_hex[2:6].lstrip('0')
    x = net_hex[6:10].lstrip('0')
    if x:
        net6 += ':' + x
    x = net_hex[10:14].lstrip('0')
    if x:
        net6 += ':' + x
    net6 += '::/64'

    return net6

def ip4to6(prefix, net, addr):
    addrs = addr.split('/')[0].split('.')
    net, cidr = net.split('/')
    nets = net.split('.')
    cidr = int(cidr)

    net_num = int(nets[0]) * 256**3 + int(nets[1]) * 256**2 + \
        int(nets[2]) * 256**1 + int(nets[3]) * 256**0
    net_hex = hex(net_num + cidr * 256**4)

    addr6 = prefix + ':' + net_hex[2:6].lstrip('0')
    x = net_hex[6:10].lstrip('0')
    if x:
        addr6 += ':' + x
    addr6 += ':' + net_hex[10:14].lstrip('0') +  ':' + addrs[0] + ':' + \
        addrs[1] + ':' + addrs[2] + ':' + addrs[3] + '/64'

    return addr6
