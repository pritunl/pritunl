from pritunl.utils.misc import check_output_logged

from pritunl.constants import *
from pritunl import ipaddress

import flask
import re
import socket
import struct
import fcntl

_tun_interfaces = set(['tun%s' % x for x in xrange(100)])
_tap_interfaces = set(['tap%s' % x for x in xrange(100)])
_br_interfaces = set(['br%s' % x for x in xrange(100)])
_sock = None
_sockfd = None

def interface_acquire(interface_type):
    if interface_type == 'tun':
        return _tun_interfaces.pop()
    elif interface_type == 'tap':
        return _tap_interfaces.pop()
    elif interface_type == 'br':
        return _br_interfaces.pop()
    else:
        raise ValueError('Unknown interface type %s' % interface_type)

def interface_release(interface_type, interface):
    if interface_type == 'tun':
        _tun_interfaces.add(interface)
    elif interface_type == 'tap':
        _tap_interfaces.add(interface)
    elif interface_type == 'br':
        _br_interfaces.add(interface)
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

def get_interfaces():
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

        netmask = re.findall(r'netmask.{0,10}' + IP_REGEX, interface, re.IGNORECASE)
        if not netmask:
            continue
        netmask = re.findall(IP_REGEX, netmask[0], re.IGNORECASE)
        if not netmask:
            continue
        data['netmask'] = netmask[0]

        broadcast = re.findall(r'broadcast.{0,10}' + IP_REGEX, interface, re.IGNORECASE)
        if not broadcast:
            continue
        broadcast = re.findall(IP_REGEX, broadcast[0], re.IGNORECASE)
        if not broadcast:
            continue
        data['broadcast'] = broadcast[0]

        interfaces[interface_name] = data

    return interfaces

def find_interface(network):
    network = ipaddress.IPNetwork(network)

    for interface, data in get_interfaces().items():
        try:
            address = ipaddress.IPAddress(data['address'])
        except ValueError:
            continue

        if address in network:
            return data
