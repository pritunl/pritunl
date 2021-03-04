from pritunl.utils.misc import check_output_logged

from pritunl.constants import *
from pritunl import ipaddress
from pritunl import settings

import flask
import re
import netifaces
import collections
import threading
import random
import pyroute2.iproute
import pyroute2.netlink
import socket

_used_interfaces = set()
_tun_interfaces = collections.deque(['tun%s' % _x for _x in range(100)])
_tap_interfaces = collections.deque(['tap%s' % _x for _x in range(100)])
_wg_interfaces = collections.deque(['wg%s' % _x for _x in range(100)])
_sock = None
_sockfd = None
_ip_route = pyroute2.iproute.IPRoute()
_ip_route_lock = threading.Lock()

def interface_acquire(interface_type):
    if interface_type == 'tun':
        intf = _tun_interfaces.popleft()
    elif interface_type == 'tap':
        intf = _tap_interfaces.popleft()
    elif interface_type == 'wg':
        intf = _wg_interfaces.popleft()
    else:
        raise ValueError('Unknown interface type %s' % interface_type)

    _used_interfaces.add(intf)
    return intf

def interface_release(interface_type, interface):
    if interface not in _used_interfaces:
        return
    _used_interfaces.remove(interface)

    if interface_type == 'tun':
        _tun_interfaces.append(interface)
    elif interface_type == 'tap':
        _tap_interfaces.append(interface)
    elif interface_type == 'wg':
        _wg_interfaces.append(interface)
    else:
        raise ValueError('Unknown interface type %s' % interface_type)

def get_remote_addr():
    if settings.app.reverse_proxy:
        forward_ip = flask.request.headers.get('PR-Forwarded-Header')
        if forward_ip:
            return forward_ip.split(',')[-1]

    forward_ip = flask.request.headers.get('PR-Forwarded-For')
    if forward_ip:
        return forward_ip

    return flask.request.remote_addr

def get_interface_address(iface):
    try:
        addrs = netifaces.ifaddresses(iface)
    except ValueError:
        return

    addrs = addrs.get(socket.AF_INET)
    if not addrs:
        return

    return addrs[0].get('addr')

def get_interface_address6(iface):
    try:
        addrs = netifaces.ifaddresses(iface)
    except ValueError:
        return

    addrs = addrs.get(socket.AF_INET6)
    if not addrs:
        return

    addr = addrs[0].get('addr')
    if addr:
        return addr.split('%')[0]

def get_ip_pool_reverse(network, network_start):
    ip_pool = network_reverse_hosts(network)
    next(ip_pool)
    next(ip_pool)

    if network_start:
        network_break = network_start

        while True:
            try:
                ip_addr = next(ip_pool)
            except StopIteration:
                ip_pool = network_reverse_hosts(network)
                next(ip_pool)
                next(ip_pool)
                return

            if ip_addr == network_break:
                break

    return ip_pool

def network_reverse_hosts(net):
    cur = int(net.broadcast_address) - 1
    end = int(net.network_address) + 1
    while cur >= end:
        cur -= 1
        yield ipaddress.ip_address(cur + 1)

def ip_to_long(ip_str):
    ip = ip_str.split('.')
    ip.reverse()
    while len(ip) < 4:
        ip.insert(1, '0')
    return sum(int(byte) << 8 * i for i, byte in enumerate(ip))

def long_to_ip(ip_num):
    return '.'.join(map(str, [
        (ip_num >> 24) & 0xff,
        (ip_num >> 16) & 0xff,
        (ip_num >> 8) & 0xff,
        ip_num & 0xff,
    ]))

def subnet_to_cidr(subnet):
    if subnet == '0.0.0.0':
        return 0
    count = 0
    while ~ip_to_long(subnet) & pow(2, count):
        count += 1
    return 32 - count

def network_addr(ip, subnet):
    return '%s/%s' % (long_to_ip(ip_to_long(ip) & ip_to_long(subnet)),
        subnet_to_cidr(subnet))

def parse_network(network):
    address = ipaddress.ip_network(network, strict=False)
    return str(address.network_address), str(address.netmask)

def get_network_gateway(network):
    return str(next(ipaddress.ip_network(network).hosts()))

def get_network_gateway_cidr(network):
    network = ipaddress.ip_network(network, strict=False)
    cidr = network.prefixlen
    return str(next(network.hosts())) + '/' + str(cidr)

def get_default_interface():
    gateways = netifaces.gateways()
    default_iface = gateways['default'].get(socket.AF_INET)
    if not default_iface:
        return
    return default_iface[1]

def get_local_address():
    default_iface = get_default_interface()
    if default_iface:
        return get_interface_address(default_iface)

def get_local_address6():
    default_iface = get_default_interface()
    if default_iface:
        return get_interface_address6(default_iface)

def get_local_networks():
    ifaces = netifaces.interfaces()
    networks = []

    for iface in ifaces:
        if iface == 'lo':
            continue

        addrs = netifaces.ifaddresses(iface).get(2)
        if not addrs:
            continue
        addrs = addrs[0]

        address = addrs.get('addr')
        if not address:
            continue

        netmask = addrs.get('netmask')
        if not netmask:
            continue

        networks.append(network_addr(address, netmask))

    return networks

def get_routes():
    routes_output = check_output_logged(['route', '-n'])

    routes = {}
    for line in routes_output.splitlines():
        line_split = line.split()
        if len(line_split) < 8 or not re.match(IP_REGEX, line_split[0]):
            continue
        routes[line_split[0]] = line_split[7]

    return routes

def get_interfaces():
    ifaces = netifaces.interfaces()
    ifaces_gateway = {}
    gateways = netifaces.gateways()
    interfaces = {}

    default_gateway = gateways.get('default', {}).get(socket.AF_INET)
    gateways = gateways.get(socket.AF_INET, []) + \
        [default_gateway] if default_gateway else []

    for gateway in gateways:
        ifaces_gateway[gateway[1]] = gateway[0]

    for iface in ifaces:
        if iface == 'lo':
            continue

        ifaddrs = netifaces.ifaddresses(iface)

        addrs = ifaddrs.get(socket.AF_INET)
        if not addrs:
            continue
        addrs = addrs[0]

        address = addrs.get('addr')
        if not address:
            continue

        broadcast = addrs.get('broadcast')
        if not broadcast:
            continue

        netmask = addrs.get('netmask')
        if not netmask:
            continue

        mac_addr = None
        mac_addrs = ifaddrs.get(netifaces.AF_LINK)
        if mac_addrs:
            mac_addr = mac_addrs[0].get('addr')

        interfaces[iface] = {
            'interface': iface,
            'mac_address': mac_addr,
            'address': address,
            'broadcast': broadcast,
            'netmask': netmask,
            'gateway': ifaces_gateway.get(iface),
        }

    return interfaces

def get_interface_mac_address(iface):
    ifaddrs = netifaces.ifaddresses(iface)
    if not ifaddrs:
        return

    mac_addrs = ifaddrs.get(netifaces.AF_LINK)
    if not mac_addrs:
        return

    return mac_addrs[0].get('addr')

def find_interface(network):
    network = ipaddress.ip_network(network, strict=False)

    for interface, data in list(get_interfaces().items()):
        try:
            address = ipaddress.ip_address(data['address'])
        except ValueError:
            continue

        if address in network and data['netmask'] == str(network.netmask):
            return data

def find_interface_addr(addr):
    match_addr = ipaddress.ip_address(addr)

    for interface, data in list(get_interfaces().items()):
        try:
            address = ipaddress.ip_address(data['address'])
        except ValueError:
            continue

        if match_addr == address:
            return data

def net4to6x64(prefix, net):
    net = net.split('/')[0]
    nets = net.split('.')

    net_num = int(nets[0]) * 256**3 + int(nets[1]) * 256**2 + \
        int(nets[2]) * 256**1 + int(nets[3]) * 256**0
    net_hex = hex(net_num)

    net6 = prefix + ':' + net_hex[2:6].lstrip('0')
    x = net_hex[6:10].lstrip('0')
    if x:
        net6 += ':' + x
    net6 += '::/64'

    return net6

def net4to6x96(prefix, net):
    prefix = str(ipaddress.IPv6Network(prefix)).split('/')[0]
    net = net.split('/')[0]
    nets = net.split('.')

    if prefix.count(':') == 5:
        prefix = prefix[:-1]

    net_num = int(nets[0]) * 256**3 + int(nets[1]) * 256**2 + \
        int(nets[2]) * 256**1 + int(nets[3]) * 256**0
    net_hex = hex(net_num)

    net6 = prefix + net_hex[2:6] + ':' + net_hex[6:10] + ':0:0/96'

    return str(ipaddress.IPv6Network(net6))

def ip4to6x64(prefix, net, addr):
    addrs = addr.split('/')[0].split('.')
    net = net.split('/')[0]
    nets = net.split('.')

    net_num = int(nets[0]) * 256**3 + int(nets[1]) * 256**2 + \
        int(nets[2]) * 256**1 + int(nets[3]) * 256**0
    net_hex = hex(net_num)

    addr6 = prefix + ':' + net_hex[2:6] + ':' + net_hex[6:10] + '::' + \
            addrs[0] + ':' + addrs[1] + ':' + addrs[2] + ':' + addrs[3]

    return str(ipaddress.IPv6Address(addr6))

def ip4to6x96(prefix, net, addr):
    prefix = str(ipaddress.IPv6Network(prefix)).split('/')[0]
    addrs = addr.split('/')[0].split('.')
    net = net.split('/')[0]
    nets = net.split('.')

    if prefix.count(':') == 5:
        prefix = prefix[:-1]

    net_num = int(nets[0]) * 256**3 + int(nets[1]) * 256**2 + \
        int(nets[2]) * 256**1 + int(nets[3]) * 256**0
    net_hex = hex(net_num)

    addr_num = int(addrs[0]) * 256**3 + int(addrs[1]) * 256**2 + \
        int(addrs[2]) * 256**1 + int(addrs[3]) * 256**0
    addr_hex = hex(addr_num)

    addr6 = prefix + net_hex[2:6] + ':' + net_hex[6:10] + ':' + \
        addr_hex[2:6] + ':' + addr_hex[6:10]

    return str(ipaddress.IPv6Address(addr6))

def add_route(dst_addr, via_addr, dev=None):
    if '/' not in dst_addr:
        dst_addr += '/32'

    if dev:
        dev = _ip_route.link_lookup(ifname=dev)[0]

    _ip_route_lock.acquire()
    try:
        _ip_route.route(
            'add',
            dst=dst_addr,
            gateway=via_addr,
            oif=dev,
        )
    except pyroute2.netlink.exceptions.NetlinkError as err:
        if err.code == 17:
            try:
                _ip_route.route(
                    'del',
                    dst=dst_addr,
                )
            except pyroute2.netlink.exceptions.NetlinkError as err:
                if err.code != 3:
                    raise
            _ip_route.route(
                'add',
                dst=dst_addr,
                gateway=via_addr,
                oif=dev,
            )
        else:
            raise
    finally:
        _ip_route_lock.release()

def del_route(dst_addr):
    if '/' not in dst_addr:
        dst_addr += '/32'

    _ip_route_lock.acquire()
    try:
        _ip_route.route(
            'del',
            dst=dst_addr,
        )
    except pyroute2.netlink.exceptions.NetlinkError as err:
        if err.code != 3:
            raise
    finally:
        _ip_route_lock.release()

def add_route6(dst_addr, via_addr, dev=None):
    if '/' not in dst_addr:
        dst_addr += '/128'

    if dev:
        dev = _ip_route.link_lookup(ifname=dev)[0]

    _ip_route_lock.acquire()
    try:
        _ip_route.route(
            'add',
            family=socket.AF_INET6,
            dst=dst_addr,
            gateway=via_addr,
            oif=dev,
        )
    except pyroute2.netlink.exceptions.NetlinkError as err:
        if err.code == 17:
            try:
                _ip_route.route(
                    'del',
                    family=socket.AF_INET6,
                    dst=dst_addr,
                )
            except pyroute2.netlink.exceptions.NetlinkError as err:
                if err.code != 3:
                    raise
            _ip_route.route(
                'add',
                family=socket.AF_INET6,
                dst=dst_addr,
                gateway=via_addr,
                oif=dev,
            )
        else:
            raise
    finally:
        _ip_route_lock.release()

def del_route6(dst_addr):
    if '/' not in dst_addr:
        dst_addr += '/128'

    _ip_route_lock.acquire()
    try:
        _ip_route.route(
            'del',
            family=socket.AF_INET6,
            dst=dst_addr,
        )
    except pyroute2.netlink.exceptions.NetlinkError as err:
        if err.code != 3:
            raise
    finally:
        _ip_route_lock.release()

def check_network_overlap(test_network, networks):
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

def check_network_private(test_network):
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

def check_network_range(test_network, start_addr, end_addr):
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

def random_ip_addr():
    return str(ipaddress.ip_address(100000000 + random.randint(
        0, 1000000000)))
