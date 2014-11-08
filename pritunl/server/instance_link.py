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
import uuid

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

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    @cached_property
    def output_label(self):
        if self.linked_host:
            return settings.local.host.name +  '->' + self.linked_host.name
        else:
            return self.server.name + '<->' + self.linked_server.name

    def generate_client_conf(self):
        if not os.path.exists(self._temp_path):
            os.makedirs(self._temp_path)
        ovpn_conf_path = os.path.join(self._temp_path, OVPN_CONF_NAME)
        self.interface = utils.tun_interface_acquire()

        if self.linked_host:
            remotes = 'remote %s %s' % (
                self.host.link_address or self.host.public_address,
                self.linked_server.port,
            )
        else:
            remotes = self.linked_server.get_key_remotes(True)

        client_conf = OVPN_INLINE_LINK_CONF % (
            uuid.uuid4().hex,
            self.interface,
            self.linked_server.protocol,
            remotes,
            CIPHERS[self.server.cipher],
            4 if self.server.debug else 1,
            8 if self.server.debug else 3,
        )

        if self.linked_server.lzo_compression != ADAPTIVE:
            client_conf += 'comp-lzo no\n'

        if self.linked_server.otp_auth:
            client_conf += 'auth-user-pass\n'

        client_conf += JUMBO_FRAMES[self.linked_server.jumbo_frames]
        client_conf += '<ca>\n%s\n</ca>\n' % self.linked_server.ca_certificate

        if self.linked_server.tls_auth:
            client_conf += '<tls-auth>\n%s\n</tls-auth>\n' % (
                self.linked_server.tls_auth_key)

        client_conf += ('<cert>\n%s\n' + \
            '</cert>\n') % utils.get_cert_block(self.user.certificate)
        client_conf += '<key>\n%s\n</key>\n' % (
            self.user.private_key.strip())

        with open(ovpn_conf_path, 'w') as ovpn_conf:
            os.chmod(ovpn_conf_path, 0600)
            ovpn_conf.write(client_conf)

        return ovpn_conf_path

    def openvpn_start(self):
        response = self.collection.update({
            '_id': self.linked_server.id,
            'links.server_id': self.server.id,
        }, {'$set': {
            'links.$.user_id': self.user.id,
        }})

        if not response['updatedExisting']:
            raise ServerLinkError('Failed to update server links')

        ovpn_conf_path = self.generate_client_conf()

        try:
            self.process = subprocess.Popen(['openvpn', ovpn_conf_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            self.server.output_link.push_output(
                traceback.format_exc(),
                label=self.output_label,
                link_server_id=self.linked_server.id,
            )
            logger.exception('Failed to start link ovpn process', 'server',
                server_id=self.server.id,
            )
            raise

    @interrupter
    def openvpn_watch(self):
        try:
            while True:
                while True:
                    line = self.process.stdout.readline()
                    if not line:
                        if self.process.poll() is not None:
                            break
                        else:
                            time.sleep(0.05)
                            continue

                    yield

                    try:
                        self.server.output_link.push_output(
                            line,
                            label=self.output_label,
                            link_server_id=self.linked_server.id,
                        )
                    except:
                        logger.exception('Failed to push link vpn ' +
                            'output', 'server',
                            server_id=self.server.id,
                        )

                    yield

                if self.stop_event.is_set():
                    break
                else:
                    logger.error('Server instance link stopped ' +
                        'unexpectedly, restarting link', 'server',
                        server_id=self.server.id,
                        link_server_id=self.linked_server.id,
                    )
                    self.openvpn_start()
                    yield interrupter_sleep(1)

            yield

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
                    logger.error('Failed to stop openvpn link process',
                        'server',
                        server_id=self.server.id,
                    )
            finally:
                if self.interface:
                    utils.tun_interface_release(self.interface)
                    self.interface = None

    def start(self):
        self.openvpn_start()

        thread = threading.Thread(target=self.openvpn_watch)
        thread.start()
        thread = threading.Thread(target=self.stop_watch)
        thread.start()

    def stop(self):
        self.stop_event.set()
