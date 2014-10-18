from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

import flask
import subprocess
import re

_interfaces = set(['tun%s' % x for x in xrange(100)])

def tun_interface_acquire():
    return _interfaces.pop()

def tun_interface_release(interface):
    _interfaces.add(interface)

def get_remote_addr():
    return flask.request.remote_addr

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
    network_split = network.split('/')
    address = network_split[0]
    cidr = int(network_split[1])
    subnet = ('255.' * (cidr / 8)) + str(
        int(('1' * (cidr % 8)).ljust(8, '0'), 2))
    subnet += '.0' * (3 - subnet.count('.'))
    return (address, subnet)

def get_local_networks():
    addresses = []
    output = subprocess.check_output(['ifconfig'])
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
