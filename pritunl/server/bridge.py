from pritunl.exceptions import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import subprocess
import threading
import collections

_lock = threading.Lock()
_bridges = {}
_bridges_lock = collections.defaultdict(threading.Lock)
_interfaces = {}

class Bridge(object):
    def __init__(self, network):
        self.host_interface_data = utils.find_interface(network)
        if not self.host_interface_data:
            logger.error('Failed to find bridged network interface', 'server',
                network=network,
            )
            raise BridgeLookupError(
                'Failed to find bridged network interface')
        self.bridge_interface = 'br' + self.host_interface_data['interface']
        self.interfaces = set()

    def start(self):
        host_int_data = self.host_interface_data
        host_interface = host_int_data['interface']
        host_address = host_int_data['address']
        host_netmask = host_int_data['netmask']
        host_broadcast = host_int_data['broadcast']
        host_gateway = host_int_data['gateway']

        utils.check_output_logged([
            'iptables',
            '-I',
            'FORWARD',
            '-i',
            self.bridge_interface,
            '-j',
            'ACCEPT',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % settings.local.host_id,
        ])
        utils.check_output_logged([
            'iptables',
            '-I',
            'INPUT',
            '-i',
            self.bridge_interface,
            '-j',
            'ACCEPT',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % settings.local.host_id,
        ])
        utils.check_output_logged([
            'ip',
            'link',
            'set',
            'down',
            host_interface,
        ])
        utils.check_output_logged([
            'brctl',
            'addbr',
            self.bridge_interface,
        ])
        utils.check_output_logged([
            'brctl',
            'addif',
            self.bridge_interface,
            host_interface,
        ])
        utils.check_output_logged([
            'ifconfig',
            host_interface,
            '0.0.0.0',
            'promisc',
            'up',
        ])
        utils.check_output_logged([
            'ifconfig',
            self.bridge_interface,
            host_address,
            'netmask',
            host_netmask,
            'broadcast',
            host_broadcast,
        ])

        if host_gateway:
            utils.check_output_logged([
                'route',
                'add',
                'default',
                'gw',
                host_gateway,
            ])

    def stop(self):
        try:
            utils.check_output_logged([
                'ip',
                'link',
                'set',
                'down',
                self.bridge_interface,
            ])
        except subprocess.CalledProcessError:
            pass
        try:
            utils.check_output_logged([
                'brctl',
                'delbr',
                self.bridge_interface,
            ])
        except subprocess.CalledProcessError:
            pass
        try:
            utils.check_output_logged([
                'iptables',
                '-D',
                'INPUT',
                '-i',
                self.bridge_interface,
                '-j',
                'ACCEPT',
                '-m', 'comment',
                '--comment', 'pritunl-%s' % settings.local.host_id,
            ])
        except subprocess.CalledProcessError:
            pass
        try:
            utils.check_output_logged([
                'iptables',
                '-D',
                'FORWARD',
                '-i',
                self.bridge_interface,
                '-j',
                'ACCEPT',
                '-m', 'comment',
                '--comment', 'pritunl-%s' % settings.local.host_id,
            ])
        except subprocess.CalledProcessError:
            pass

        host_int_data = self.host_interface_data
        host_interface = host_int_data['interface']
        host_address = host_int_data['address']
        host_netmask = host_int_data['netmask']
        host_broadcast = host_int_data['broadcast']
        host_gateway = host_int_data['gateway']

        utils.check_output_logged([
            'ip',
            'link',
            'set',
            'down',
            host_interface,
        ])

        utils.check_output_logged([
            'ip',
            'link',
            'set',
            'up',
            host_interface,
        ])

        utils.check_output_logged([
            'ifconfig',
            host_interface,
            host_address,
            'netmask',
            host_netmask,
            'broadcast',
            host_broadcast,
        ])
        if host_gateway:
            try:
                utils.check_output_logged([
                    'route',
                    'add',
                    'default',
                    'gw',
                    host_gateway,
                ])
            except subprocess.CalledProcessError:
                pass

    def add_interface(self, interface):
        self.interfaces.add(interface)

        utils.check_output_logged([
            'openvpn',
            '--mktun',
            '--dev',
            interface,
        ])
        utils.check_output_logged([
            'brctl',
            'addif',
            self.bridge_interface,
            interface,
        ])
        utils.check_output_logged([
            'ifconfig',
            interface,
            '0.0.0.0',
            'promisc',
            'up',
        ])

    def rem_interface(self, interface):
        if interface not in self.interfaces:
            return

        try:
            utils.check_output_logged([
                'ip',
                'link',
                'set',
                'down',
                interface,
            ])
        except subprocess.CalledProcessError:
            pass
        try:
            utils.check_output_logged([
                'brctl',
                'delif',
                self.bridge_interface,
                interface,
            ])
        except subprocess.CalledProcessError:
            pass
        try:
            utils.check_output_logged([
                'openvpn',
                '--rmtun',
                '--dev',
                interface,
            ])
        except subprocess.CalledProcessError:
            pass

        self.interfaces.remove(interface)

def add_interface(network, interface):
    _lock.acquire()
    bridge_lock = _bridges_lock[network]
    bridge_lock.acquire()
    _lock.release()
    try:
        bridge = _bridges.get(network)
        if not bridge:
            bridge = Bridge(network)
            try:
                bridge.start()
            except:
                try:
                    bridge.stop()
                except:
                    pass
                raise
        _bridges[network] = bridge

        bridge.add_interface(interface)

        return bridge.bridge_interface, bridge.host_interface_data
    finally:
        bridge_lock.release()

def rem_interface(network, interface):
    _lock.acquire()
    bridge_lock = _bridges_lock[network]
    bridge_lock.acquire()
    _lock.release()
    try:
        bridge = _bridges.get(network)
        if not bridge:
            return

        bridge.rem_interface(interface)

        if len(bridge.interfaces) == 0:
            bridge.stop()
            _bridges.pop(network)
    finally:
        bridge_lock.release()
