from pritunl import utils
from pritunl import logger

import itertools
import subprocess
import time
import threading

_global_lock = threading.Lock()

class Iptables(object):
    def __init__(self):
        self._routes = set()
        self._routes6 = set()
        self._nat_routes = {}
        self._nat_routes6 = {}
        self._nat_networks = set()
        self._nat_networks6 = set()
        self._accept = []
        self._accept6 = []
        self._drop = []
        self._drop6 = []
        self._other = []
        self._other6 = []
        self._accept_all = False
        self._lock = threading.Lock()
        self.id = None
        self.server_addr = None
        self.server_addr6 = None
        self.virt_interface = None
        self.virt_network = None
        self.virt_network6 = None
        self.ipv6_firewall = None
        self.inter_client = None
        self.ipv6 = False
        self.cleared = False
        self.restrict_routes = False

    @property
    def comment(self):
        return [
            '-m', 'comment',
            '--comment', 'pritunl_%s' % self.id,
        ]

    def add_route(self, network, nat=False, nat_interface=None):
        if self.cleared:
            return

        if network == '0.0.0.0/0' or network == '::/0':
            self._accept_all = True

        if ':' in network:
            if nat:
                self._nat_routes6[network] = nat_interface
            else:
                self._routes6.add(network)
        else:
            if nat:
                self._nat_routes[network] = nat_interface
            else:
                self._routes.add(network)

    def add_nat_network(self, network):
        if self.cleared:
            return

        if ':' in network:
            self._nat_networks6.add(network)
        else:
            self._nat_networks.add(network)

    def add_rule(self, rule):
        if self.cleared:
            return

        self._lock.acquire()
        try:
            self._other.append(rule)
            if not self._exists_iptables_rule(rule):
                self._insert_iptables_rule(rule)
        finally:
            self._lock.release()

    def add_rule6(self, rule):
        if self.cleared:
            return

        self._lock.acquire()
        try:
            self._other6.append(rule)
            if not self._exists_iptables_rule(rule, ipv6=True):
                self._insert_iptables_rule(rule, ipv6=True)
        finally:
            self._lock.release()

    def remove_rule(self, rule):
        if self.cleared:
            return

        self._lock.acquire()
        try:
            self._other.remove(rule)
            self._remove_iptables_rule(rule)
        except ValueError:
            logger.warning('Lost iptables rule', 'iptables',
                rule=rule,
            )
        finally:
            self._lock.release()

    def remove_rule6(self, rule):
        if self.cleared:
            return

        self._lock.acquire()
        try:
            self._other6.remove(rule)
            self._remove_iptables_rule(rule, ipv6=True)
        except ValueError:
            logger.warning('Lost ip6tables rule', 'iptables',
                rule=rule,
            )
        finally:
            self._lock.release()

    def _generate_input(self):
        if self._accept_all:
            self._accept.append([
                'INPUT',
                '-i', self.virt_interface,
                '-j', 'ACCEPT',
            ])

            if self.ipv6_firewall:
                self._accept6.append([
                    'INPUT',
                    '-d', self.virt_network6,
                    '-m', 'conntrack',
                    '--ctstate','RELATED,ESTABLISHED',
                    '-j', 'ACCEPT',
                ])
                self._accept6.append([
                    'INPUT',
                    '-d', self.virt_network6,
                    '-p', 'icmpv6',
                    '-m', 'conntrack',
                    '--ctstate', 'NEW',
                    '-j', 'ACCEPT',
                ])
                self._drop6.append([
                    'INPUT',
                    '-d', self.virt_network6,
                    '-j', 'DROP',
                ])
            else:
                self._accept6.append([
                    'INPUT',
                    '-i', self.virt_interface,
                    '-j', 'ACCEPT',
                ])

            return

        if self.inter_client:
            self._accept.append([
                'INPUT', '-i', self.virt_interface,
                '-d', self.virt_network,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'INPUT', '-i', self.virt_interface,
                '-d', self.virt_network6,
                '-j', 'ACCEPT',
            ])
        else:
            self._accept.append([
                'INPUT', '-i', self.virt_interface,
                '-d', self.server_addr,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'INPUT', '-i', self.virt_interface,
                '-d', self.server_addr6,
                '-j', 'ACCEPT',
            ])

        for route in itertools.chain(self._routes, self._nat_routes.keys()):
            self._accept.append([
                'INPUT',
                '-i', self.virt_interface,
                '-d', route,
                '-j', 'ACCEPT',
            ])

        for route in itertools.chain(self._routes6, self._nat_routes6.keys()):
            self._accept6.append([
                'INPUT',
                '-i', self.virt_interface,
                '-d', route,
                '-j', 'ACCEPT',
            ])

        self._drop.append([
            'INPUT',
            '-i', self.virt_interface,
            '-j', 'DROP',
        ])
        self._drop6.append([
            'INPUT',
            '-i', self.virt_interface,
            '-j', 'DROP',
        ])

    def _generate_output(self):
        if self._accept_all:
            self._accept.append([
                'OUTPUT',
                '-o', self.virt_interface,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'OUTPUT',
                '-o', self.virt_interface,
                '-j', 'ACCEPT',
            ])
            return

        if self.inter_client:
            self._accept.append([
                'OUTPUT', '-o', self.virt_interface,
                '-s', self.virt_network,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'OUTPUT', '-o', self.virt_interface,
                '-s', self.virt_network6,
                '-j', 'ACCEPT',
            ])
        else:
            self._accept.append([
                'OUTPUT', '-o', self.virt_interface,
                '-s', self.server_addr,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'OUTPUT', '-o', self.virt_interface,
                '-s', self.server_addr6,
                '-j', 'ACCEPT',
            ])

        for route in itertools.chain(self._routes, self._nat_routes.keys()):
            self._accept.append([
                'OUTPUT',
                '-o', self.virt_interface,
                '-s', route,
                '-j', 'ACCEPT',
            ])

        for route in itertools.chain(self._routes6, self._nat_routes6.keys()):
            self._accept6.append([
                'OUTPUT',
                '-o', self.virt_interface,
                '-s', route,
                '-j', 'ACCEPT',
            ])

        self._drop.append([
            'OUTPUT',
            '-o', self.virt_interface,
            '-j', 'DROP',
        ])
        self._drop6.append([
            'OUTPUT',
            '-o', self.virt_interface,
            '-j', 'DROP',
        ])

    def _generate_forward(self):
        if self._accept_all:
            self._accept.append([
                'FORWARD',
                '-i', self.virt_interface,
                '-j', 'ACCEPT',
            ])
            self._accept.append([
                'FORWARD',
                '-o', self.virt_interface,
                '-j', 'ACCEPT',
            ])

            if self.ipv6_firewall:
                self._accept6.append([
                    'FORWARD',
                    '-d', self.virt_network6,
                    '-m', 'conntrack',
                    '--ctstate', 'RELATED,ESTABLISHED',
                    '-j', 'ACCEPT',
                ])
                self._accept6.append([
                    'FORWARD',
                    '-d', self.virt_network6,
                    '-p', 'icmpv6',
                    '-m', 'conntrack',
                    '--ctstate', 'NEW',
                    '-j', 'ACCEPT',
                ])
                self._drop6.append([
                    'FORWARD',
                    '-d', self.virt_network6,
                    '-j', 'DROP',
                ])
            else:
                self._accept6.append([
                    'FORWARD',
                    '-i', self.virt_interface,
                    '-j', 'ACCEPT',
                ])
                self._accept6.append([
                    'FORWARD',
                    '-o', self.virt_interface,
                    '-j', 'ACCEPT',
                ])

            return

        if self.inter_client:
            self._accept.append([
                'FORWARD', '-i', self.virt_interface,
                '-d', self.virt_network,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'FORWARD', '-i', self.virt_interface,
                '-d', self.virt_network6,
                '-j', 'ACCEPT',
            ])
            self._accept.append([
                'FORWARD', '-o', self.virt_interface,
                '-s', self.virt_network,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'FORWARD', '-o', self.virt_interface,
                '-s', self.virt_network6,
                '-j', 'ACCEPT',
            ])

        for route in self._routes:
            self._accept.append([
                'FORWARD',
                '-i', self.virt_interface,
                '-d', route,
                '-j', 'ACCEPT',
            ])
            self._accept.append([
                'FORWARD',
                '-o', self.virt_interface,
                '-s', route,
                '-j', 'ACCEPT',
            ])

        for route in self._routes6:
            self._accept6.append([
                'FORWARD',
                '-i', self.virt_interface,
                '-d', route,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'FORWARD',
                '-o', self.virt_interface,
                '-s', route,
                '-j', 'ACCEPT',
            ])

        for route in self._nat_routes.keys():
            self._accept.append([
                'FORWARD',
                '-i', self.virt_interface,
                '-d', route,
                '-j', 'ACCEPT',
            ])
            self._accept.append([
                'FORWARD',
                '-o', self.virt_interface,
                '-m', 'conntrack',
                '--ctstate', 'RELATED,ESTABLISHED',
                '-s', route,
                '-j', 'ACCEPT',
            ])

        for route in self._nat_routes6.keys():
            self._accept6.append([
                'FORWARD',
                '-i', self.virt_interface,
                '-d', route,
                '-j', 'ACCEPT',
            ])
            self._accept6.append([
                'FORWARD',
                '-o', self.virt_interface,
                '-m', 'conntrack',
                '--ctstate', 'RELATED,ESTABLISHED',
                '-s', route,
                '-j', 'ACCEPT',
            ])

        self._drop.append([
            'FORWARD',
            '-i', self.virt_interface,
            '-j', 'DROP',
        ])
        self._drop.append([
            'FORWARD',
            '-o', self.virt_interface,
            '-j', 'DROP',
        ])
        self._drop6.append([
            'FORWARD',
            '-i', self.virt_interface,
            '-j', 'DROP',
        ])
        self._drop6.append([
            'FORWARD',
            '-o', self.virt_interface,
            '-j', 'DROP',
        ])

    def _generate_post_routing(self):
        all_interface = None
        all_interface6 = None

        for route, interface in self._nat_routes.items():
            if route == '0.0.0.0/0':
                all_interface = interface
                continue

            for nat_network in self._nat_networks:
                self._accept.append([
                    'POSTROUTING',
                    '-t', 'nat',
                    '-s', nat_network,
                    '-d', route,
                    '-o', interface,
                    '-j', 'MASQUERADE',
                ])

        for route, interface in self._nat_routes6.items():
            if route == '::/0':
                all_interface6 = interface
                continue

            for nat_network in self._nat_networks6:
                self._accept6.append([
                    'POSTROUTING',
                    '-t', 'nat',
                    '-s', nat_network,
                    '-d', route,
                    '-o', interface,
                    '-j', 'MASQUERADE',
                ])

        if self._accept_all and all_interface:
            for nat_network in self._nat_networks:
                self._accept.append([
                    'POSTROUTING',
                    '-t', 'nat',
                    '-s', nat_network,
                    '-o', all_interface,
                    '-j', 'MASQUERADE',
                ])
            for nat_network in self._nat_networks6:
                self._accept6.append([
                    'POSTROUTING',
                    '-t', 'nat',
                    '-s', nat_network,
                    '-o', all_interface6,
                    '-j', 'MASQUERADE',
                ])

    def generate(self):
        if self.cleared:
            return

        self._accept = []
        self._accept6 = []
        self._drop = []
        self._drop6 = []

        self._generate_input()
        self._generate_output()
        self._generate_forward()
        self._generate_post_routing()

    def _parse_rule(self, rule):
        return rule + [
            '-m', 'comment',
            '--comment', 'pritunl_%s' % self.id,
        ]

    def _exists_iptables_rule(self, rule, ipv6=False):
        rule = self._parse_rule(rule)

        _global_lock.acquire()
        try:
            process = subprocess.Popen(
                ['ip6tables' if ipv6 else 'iptables', '-C'] + rule,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if process.wait():
                return False
            return True
        finally:
            _global_lock.release()

    def _remove_iptables_rule(self, rule, ipv6=False):
        rule = self._parse_rule(rule)

        _global_lock.acquire()
        try:
            process = subprocess.Popen(
                ['ip6tables' if ipv6 else 'iptables', '-D'] + rule,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if process.wait():
                return False
            return True
        finally:
            _global_lock.release()

    def _insert_iptables_rule(self, rule, ipv6=False):
        rule = self._parse_rule(rule)

        _global_lock.acquire()
        try:
            for i in xrange(3):
                try:
                    utils.check_output_logged(
                        ['ip6tables' if ipv6 else 'iptables', '-I'] + rule)
                    break
                except:
                    if i == 2:
                        raise
                    logger.error(
                        'Failed to insert iptables rule, retrying...',
                        'instance',
                        rule=rule,
                    )
                time.sleep(1)
        finally:
            _global_lock.release()

    def _append_iptables_rule(self, rule, ipv6=False):
        rule = self._parse_rule(rule)

        _global_lock.acquire()
        try:
            for i in xrange(3):
                try:
                    utils.check_output_logged(
                        ['ip6tables' if ipv6 else 'iptables', '-A'] + rule)
                    break
                except:
                    if i == 2:
                        raise
                    logger.error(
                        'Failed to insert iptables rule, retrying...',
                        'instance',
                        rule=rule,
                    )
                time.sleep(1)
        finally:
            _global_lock.release()

    def upsert_rules(self, log=False):
        if self.cleared:
            return

        self._lock.acquire()
        try:
            if not self._accept:
                return

            for rule in self._accept:
                if not self._exists_iptables_rule(rule):
                    if log:
                        logger.error(
                            'Unexpected loss of iptables rule, ' +
                                'adding again...',
                            'instance',
                            rule=rule,
                        )
                    self._insert_iptables_rule(rule)

            if self.ipv6:
                for rule in self._accept6:
                    if not self._exists_iptables_rule(rule, ipv6=True):
                        if log:
                            logger.error(
                                'Unexpected loss of ip6tables rule, ' +
                                    'adding again...',
                                'instance',
                                rule=rule,
                            )
                        self._insert_iptables_rule(rule, ipv6=True)

            if self.restrict_routes:
                for rule in self._drop:
                    if not self._exists_iptables_rule(rule):
                        if log:
                            logger.error(
                                'Unexpected loss of iptables drop rule, ' +
                                    'adding again...',
                                'instance',
                                rule=rule,
                            )
                        self._append_iptables_rule(rule)

                if self.ipv6:
                    for rule in self._drop6:
                        if not self._exists_iptables_rule(rule, ipv6=True):
                            if log:
                                logger.error(
                                    'Unexpected loss of ip6tables drop ' +
                                        'rule, adding again...',
                                    'instance',
                                    rule=rule,
                                )
                            self._append_iptables_rule(rule, ipv6=True)
        finally:
            self._lock.release()

    def clear_rules(self):
        if self.cleared:
            return

        self._lock.acquire()
        try:
            self.cleared = True

            for rule in self._accept + self._other:
                self._remove_iptables_rule(rule)

            if self.ipv6:
                for rule in self._accept6 + self._other6:
                    self._remove_iptables_rule(rule, ipv6=True)

            if self.restrict_routes:
                for rule in self._drop:
                    self._remove_iptables_rule(rule)

                if self.ipv6:
                    for rule in self._drop6:
                        self._remove_iptables_rule(rule, ipv6=True)

            self._accept = None
            self._accept6 = None
            self._other = None
            self._other6 = None
            self._drop = None
            self._drop6 = None
        finally:
            self._lock.release()
