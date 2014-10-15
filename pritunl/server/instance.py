from pritunl.server.output import ServerOutput
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
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

_resource_locks = collections.defaultdict(threading.Lock)
_interfaces = set(['tun%s' % x for x in xrange(128)])

class ServerInstance(object):
    def __init__(self, server):
        self.server = server
        self.instance_id = str(bson.ObjectId())
        self.resource_lock = None
        self.interrupt = False
        self.clean_exit = False
        self.clients = {}
        self.client_count = 0
        self.interface = None
        self._temp_path = utils.get_temp_path()
        self.thread_semaphores = threading.Semaphore(3)
        for _ in xrange(3):
            self.thread_semaphores.acquire()

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    def get_cursor_id(self):
        return messenger.get_cursor_id('servers')

    def publish(self, message, transaction=None, extra=None):
        extra = extra or {}
        extra.update({
            'server_id': self.server.id,
        })
        messenger.publish('servers', message,
            extra=extra, transaction=transaction)

    def subscribe(self, cursor_id=None, timeout=None):
        for msg in messenger.subscribe('servers', cursor_id=cursor_id,
                timeout=timeout):
            if msg.get('server_id') == self.server.id:
                yield msg

    def resources_acquire(self):
        if self.resource_lock:
            raise TypeError('Server resource lock already set')
        self.resource_lock = _resource_locks[self.server.id]
        self.resource_lock.acquire()
        self.interface = _interfaces.pop()

    def resources_release(self):
        if self.resource_lock:
            self.resource_lock.release()
            self.interface.add(self.interface)
            self.interface = None

    def generate_ovpn_conf(self):
        logger.debug('Generating server ovpn conf. %r' % {
            'server_id': self.id,
        })

        if not self.server.primary_organization or \
                not self.server.primary_user:
            self.server.create_primary_user()

        primary_org = organization.get_org(
            id=self.server.primary_organization)
        if not primary_org:
            self.server.create_primary_user()
            primary_org = organization.get_org(
                id=self.server.primary_organization)

        primary_user = primary_org.get_user(self.server.primary_user)
        if not primary_user:
            self.server.create_primary_user()
            primary_org = organization.get_org(
                id=self.server.primary_organization)
            primary_user = primary_org.get_user(self.server.primary_user)

        tls_verify_path = os.path.join(self._temp_path,
            TLS_VERIFY_NAME)
        user_pass_verify_path = os.path.join(self._temp_path,
            USER_PASS_VERIFY_NAME)
        client_connect_path = os.path.join(self._temp_path,
            CLIENT_CONNECT_NAME)
        client_disconnect_path = os.path.join(self._temp_path,
            CLIENT_DISCONNECT_NAME)
        ovpn_status_path = os.path.join(self._temp_path,
            OVPN_STATUS_NAME)
        ovpn_conf_path = os.path.join(self._temp_path,
            OVPN_CONF_NAME)

        auth_host = settings.conf.bind_addr
        if auth_host == '0.0.0.0':
            auth_host = 'localhost'
        for script, script_path in (
                    (TLS_VERIFY_SCRIPT, tls_verify_path),
                    (USER_PASS_VERIFY_SCRIPT, user_pass_verify_path),
                    (CLIENT_CONNECT_SCRIPT, client_connect_path),
                    (CLIENT_DISCONNECT_SCRIPT, client_disconnect_path),
                ):
            with open(script_path, 'w') as script_file:
                os.chmod(script_path, 0755) # TODO
                script_file.write(script % (
                    settings.app.server_api_key,
                    '/dev/null', # TODO
                    'https' if settings.conf.ssl else 'http',
                    auth_host,
                    settings.conf.port,
                    self.server.id,
                ))

        push = ''
        if self.server.server.mode == LOCAL_TRAFFIC:
            for network in self.server.local_networks:
                push += 'push "route %s %s"\n' % utils.parse_network(network)
        elif self.server.mode == VPN_TRAFFIC:
            pass
        else:
            push += 'push "redirect-gateway"\n'
        for dns_server in self.server.dns_servers:
            push += 'push "dhcp-option DNS %s"\n' % dns_server
        if self.server.search_domain:
            push += 'push "dhcp-option DOMAIN %s"\n' % (
                self.server.search_domain)

        server_conf = OVPN_INLINE_SERVER_CONF % (
            self.server.port,
            self.server.protocol,
            self.interface,
            tls_verify_path,
            client_connect_path,
            client_disconnect_path,
            '%s %s' % utils.parse_network(self.server.network),
            ovpn_status_path,
            4 if self.server.debug else 1,
            8 if self.server.debug else 3,
        )

        if self.server.otp_auth:
            server_conf += 'auth-user-pass-verify %s via-file\n' % (
                user_pass_verify_path)

        if self.server.lzo_compression:
            server_conf += 'comp-lzo\npush "comp-lzo"\n'

        if self.server.mode in (LOCAL_TRAFFIC, VPN_TRAFFIC):
            server_conf += 'client-to-client\n'

        if push:
            server_conf += push

        server_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
            self.server.ca_certificate)
        server_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
            primary_user.certificate)
        server_conf += '<key>\n%s\n</key>\n' % primary_user.private_key
        server_conf += '<dh>\n%s\n</dh>\n' % self.server.dh_params

        with open(ovpn_conf_path, 'w') as ovpn_conf:
            os.chmod(ovpn_conf_path, 0600)
            ovpn_conf.write(server_conf)

    def enable_ip_forwarding(self):
        logger.debug('Enabling ip forwarding. %r' % {
            'server_id': self.id,
            'rule': rule,
        })

        try:
            subprocess.check_call(['sysctl', '-w', 'net.ipv4.ip_forward=1'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to enable IP forwarding. %r' % {
                'server_id': self.server.id,
            })
            raise
