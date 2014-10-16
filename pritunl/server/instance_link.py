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
import select

class ServerInstanceLink(object):
    def __init__(self, server, linked_server, host_id=None):
        self.server = server
        self.linked_server = linked_server
        self.stop_event = threading.Event()

        if host_id:
            self.host = host.get_host(id=host_id)
        else:
            self.host = None

        self.user = settings.local.host.get_link_user(
            self.linked_server.organizations[0])

        self.process = None
        self._temp_path = utils.get_temp_path()

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    def generate_client_conf(self):
        os.makedirs(self._temp_path)
        ovpn_conf_path = os.path.join(self._temp_path, OVPN_CONF_NAME)

        client_conf = OVPN_INLINE_CLIENT_CONF % (
            '{}',
            self.linked_server.protocol,
            'remote %s %s' % (self.host.public_address,
                self.linked_server.port),
        )

        client_conf += 'route-nopull\n'

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

        try:
            self.process = subprocess.Popen(['openvpn', ovpn_conf_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            self.server.output_link.push_output(traceback.format_exc())
            logger.exception('Failed to start link ovpn process. %r' % {
                'server_id': self.server.id,
            })
            raise

    def openvpn_watch(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None:
                    break
                else:
                    time.sleep(0.05)
                    continue

            try:
                label = settings.local.host.name + '->' + self.host.name
                self.server.output_link.push_output(line, label=label)
            except:
                logger.exception('Failed to push link vpn output. %r', {
                    'server_id': self.server.id,
                })

    def stop_watch(self):
        try:
            self.stop_event.wait()
        finally:
            if not utils.stop_process(self.process):
                logger.error('Failed to stop openvpn link process. %r' % {
                    'server_id': self.server.id,
                })

    def start(self):
        ovpn_conf_path = self.generate_client_conf()
        self.openvpn_start()

        thread = threading.Thread(target=self.openvpn_watch)
        thread.start()
        thread = threading.Thread(target=self.stop_watch)
        thread.start()

    def stop(self):
        self.stop_event.set()
