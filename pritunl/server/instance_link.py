from pritunl.server.output import ServerOutput
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import ipaddress
from pritunl import logger
from pritunl import host
from pritunl import utils
from pritunl import mongo
from pritunl import queue
from pritunl import transaction
from pritunl import event
from pritunl import messenger
from pritunl import organization
from pritunl import listener

import os
import signal
import time
import datetime
import subprocess
import threading
import traceback
import re
import bson
import pymongo
import random
import collections
import select

class ServerInstanceLink(object):
    def __init__(self, server, linked_server, linked_host=None):
        self.server = server
        self.linked_server = linked_server
        self.linked_host = linked_host

        self.process = None
        self.interface = None
        self.stop_event = threading.Event()
        self.user = settings.local.host.get_link_user(
            self.linked_server.organizations[0])
        self._temp_path = utils.get_temp_path()

        self.linked_server.links[self.server.id] = self.user.id
        self.linked_server.commit('links')

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    @cached_property
    def output_label(self):
        if self.linked_host:
            return settings.local.host.name +  '->' + self.linked_host.name
        else:
            return self.server.name + '<->' + self.linked_server.name

    # TODO merge with instance.generate_iptables_rules
    def generate_iptables_rules(self):
        rules = []

        rules.append(['INPUT', '-i', self.interface, '-j', 'ACCEPT'])
        rules.append(['FORWARD', '-i', self.interface, '-j', 'ACCEPT'])

        rules.append([
            'POSTROUTING',
            '-t', 'nat',
            '-s', self.server.network,
            '-d', self.linked_server.network,
            '-o', self.interface,
            '-j', 'MASQUERADE',
        ])

        extra_args = [
            '--wait',
            '-m', 'comment',
            '--comment', 'pritunl_%s' % self.server.id,
        ]
        rules = [x + extra_args for x in rules]

        return rules

    def exists_iptables_rules(self, rule):
        cmd = ['iptables', '-C'] + rule
        return (cmd, subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE))

    def set_iptables_rules(self):
        logger.debug('Setting iptables rules. %r' % {
            'server_id': self.server.id,
        })

        processes = {}
        poller = select.epoll()
        self.iptables_rules = self.generate_iptables_rules()

        for rule in self.iptables_rules:
            cmd, process = self.exists_iptables_rules(rule)
            fileno = process.stdout.fileno()

            processes[fileno] = (cmd, process, ['iptables', '-A'] + rule)
            poller.register(fileno, select.EPOLLHUP)

        try:
            while True:
                for fd, event in poller.poll(timeout=8):
                    cmd, process, next_cmd = processes.pop(fd)
                    poller.unregister(fd)

                    if next_cmd:
                        if process.poll():
                            process = subprocess.Popen(next_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                            )
                            fileno = process.stdout.fileno()

                            processes[fileno] = (next_cmd, process, None)
                            poller.register(fileno, select.EPOLLHUP)
                    else:
                        retcode = process.poll()
                        if retcode:
                            std_out, err_out = process.communicate()
                            raise subprocess.CalledProcessError(
                                retcode, cmd, output=err_out)

                    if not processes:
                        return

        except subprocess.CalledProcessError as error:
            logger.exception('Failed to apply iptables ' + \
                'routing rule. %r' % {
                    'server_id': self.server.id,
                    'rule': rule,
                    'output': error.output,
                })
            raise

    def clear_iptables_rules(self):
        logger.debug('Clearing iptables rules. %r' % {
            'server_id': self.server.id,
        })

        processes = []

        for rule in self.iptables_rules:
            process = subprocess.Popen(['iptables', '-D'] + rule,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(process)

        for process in processes:
            process.wait()

    def generate_client_conf(self):
        os.makedirs(self._temp_path)
        ovpn_conf_path = os.path.join(self._temp_path, OVPN_CONF_NAME)
        self.interface = utils.tun_interface_acquire()

        if self.linked_host:
            remotes = 'remote %s %s' % (
                self.host.public_address,
                self.linked_server.port,
            )
        else:
            remotes = self.linked_server.get_key_remotes()

        client_conf = OVPN_INLINE_LINK_CONF % (
            self.interface,
            self.linked_server.protocol,
            remotes,
            4 if self.server.debug else 1,
            8 if self.server.debug else 3,
        )

        if self.server.lzo_compression != ADAPTIVE:
            client_conf += 'comp-lzo no\n'

        client_conf += PERF_MODES[self.server.performance_mode]
        client_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
            self.server.ca_certificate)
        client_conf += ('<cert>\n%s\n' + \
            '</cert>\n') % utils.get_cert_block(self.user.certificate)
        client_conf += '<key>\n%s\n</key>\n' % (
            self.user.private_key.strip())

        with open(ovpn_conf_path, 'w') as ovpn_conf:
            os.chmod(ovpn_conf_path, 0600)
            ovpn_conf.write(client_conf)

        return ovpn_conf_path

    def openvpn_start(self):
        ovpn_conf_path = os.path.join(self._temp_path, OVPN_CONF_NAME)

        self.set_iptables_rules()

        try:
            self.process = subprocess.Popen(['openvpn', ovpn_conf_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            self.server.output_link.push_output(
                traceback.format_exc(),
                label=self.output_label,
                link_server_id=self.linked_server.id,
            )
            logger.exception('Failed to start link ovpn process. %r' % {
                'server_id': self.server.id,
            })
            raise

    def openvpn_watch(self):
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        break
                    else:
                        time.sleep(0.05)
                        continue

                try:
                    self.server.output_link.push_output(
                        line,
                        label=self.output_label,
                        link_server_id=self.linked_server.id,
                    )
                except:
                    logger.exception('Failed to push link vpn output. %r', {
                        'server_id': self.server.id,
                    })
        finally:
            if self.interface:
                utils.tun_interface_release(self.interface)
                self.interface = None

    @interrupter
    def stop_watch(self):
        try:
            while True:
                if self.stop_event.wait(1):
                    return
                yield
        finally:
            try:
                if not utils.stop_process(self.process):
                    logger.error('Failed to stop openvpn link process. %r' % {
                        'server_id': self.server.id,
                    })
            finally:
                if self.interface:
                    utils.tun_interface_release(self.interface)
                    self.interface = None

    def start(self):
        ovpn_conf_path = self.generate_client_conf()
        self.openvpn_start()

        thread = threading.Thread(target=self.openvpn_watch)
        thread.start()
        thread = threading.Thread(target=self.stop_watch)
        thread.start()

    def stop(self):
        self.stop_event.set()
