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
import socket

class ServerInstanceCom(object):
    def __init__(self, server, instance):
        self.server = server
        self.instance = instance
        self.sock = None
        self.socket_path = instance.management_socket_path
        self.client = None
        self.clients = {}
        self.client_auth = False

    def client_connect(self, client):
        from pritunl.server.utils import get_by_id

        org_id = bson.ObjectId(client['org_id'])
        user_id = bson.ObjectId(client['user_id'])
        username = client['username'] # TODO
        password = client['password']
        vpn_ver = client['vpn_ver']
        ssl_ver = client['ssl_ver']
        mac_addr = client['mac_addr']
        remote_ip = client['remote_ip']
        device_key = '%s-%s-%s' % (remote_ip, vpn_ver, ssl_ver)

        org = self.server.get_org(org_id, fields=['_id'])
        if not org:
            self.send_client_deny(client, 'Organization is not valid')
            return

        user = org.get_user(user_id, fields=['_id', 'name', 'disabled'])
        if not user:
            self.send_client_deny(client, 'User is not valid')
            return

        client_conf = ''

        link_svr_id = None
        for link_doc in self.server.links:
            if link_doc['user_id'] == user.id:
                link_svr_id = link_doc['server_id']
                break

        if link_svr_id:
            link_svr = get_by_id(link_svr_id,
                fields=['_id', 'network', 'local_networks'])
            client_conf += 'iroute %s %s\n' % utils.parse_network(
                link_svr.network)
            for local_network in link_svr.local_networks:
                push += 'iroute %s %s\n' % utils.parse_network(
                    local_network)

        remote_ip_addr = None
        devices = self.clients.get(user_id)
        if devices:
            for device in devices:
                if device['mac_addr'] == mac_addr:
                    remote_ip_addr = device['remote_ip_addr']
                    break
            if not remote_ip_addr:
                for device in devices:
                    dev_key = '%s-%s-%s' % (device['remote_ip'],
                        device['vpn_ver'], device['ssl_ver'])
                    if dev_key == device_key:
                        remote_ip_addr = device['remote_ip_addr']
                        break

        remote_ip_addr = self.server.get_ip_addr(org.id, user_id)
        if remote_ip_addr:
            client_conf += 'ifconfig-push %s %s\n' % utils.parse_network(
                remote_ip_addr)

        self.send_client_auth(client, client_conf)

    def send_client_auth(self, client, client_conf):
        self.sock.send('client-auth %s %s\n%s\nEND\n' % (
            client['client_id'], client['key_id'], client_conf))
        self.push_output('User auth successful %s %s' % (
            client['user_id'], client['org_id']))

    def send_client_deny(self, client, reason):
        self.sock.send('client-deny %s %s "%s"\n' % (
            client['client_id'], client['key_id'], reason))
        self.push_output('ERROR User auth failed "%s"' % reason)

    def push_output(self, message):
        timestamp = datetime.datetime.utcnow().strftime(
            '%a %b  %d %H:%M:%S %Y').replace('  0', '   ', 1).replace(
            '  ', ' ', 1)
        self.server.output.push_output('%s %s' % (timestamp, message))

    def parse_line(self, line):
        if self.client:
            if line == '>CLIENT:ENV,END':
                self.client_connect(self.client)
                self.client = None
            elif line[:11] == '>CLIENT:ENV':
                env_key, env_val = line[12:].split('=', 1)
                if env_key == 'tls_id_0':
                    tls_env = ''.join(x for x in env_val if x in VALID_CHARS)
                    o_index = tls_env.find('O=')
                    cn_index = tls_env.find('CN=')
                    if o_index < 0 or cn_index < 0:
                        self.send_client_deny(self.client,
                            'Failed to parse org_id and user_id')
                        self.client = None
                        return
                    if o_index > cn_index:
                        org_id = tls_env[o_index + 2:]
                        user_id = tls_env[3:o_index]
                    else:
                        org_id = tls_env[2:cn_index]
                        user_id = tls_env[cn_index + 3:]

                    self.client['org_id'] = org_id
                    self.client['user_id'] = user_id
                elif env_key == 'IV_VER':
                    self.client['vpn_ver'] = env_val
                elif env_key == 'IV_SSL':
                    self.client['ssl_ver'] = env_val
                elif env_key == 'IV_HWADDR':
                    self.client['mac_addr'] = env_val
                elif env_key == 'untrusted_ip':
                    self.client['remote_ip'] = env_val
                elif env_key == 'username':
                    self.client['username'] = env_val
                elif env_key == 'password':
                    self.client['password'] = env_val
                elif env_key == 'password':
                    self.client['password'] = env_val
        elif line[:14] in ('>CLIENT:CONNEC', '>CLIENT:REAUTH'):
            _, client_id, key_id = line.split(',')
            self.client = {
                'client_id': client_id,
                'key_id': key_id,
            }
        else:
            print 'line:', line

    def wait_for_socket(self):
        for _ in xrange(10000):
            if os.path.exists(self.socket_path):
                return
            time.sleep(0.001)

    def _socket_thread(self):
        data = ''
        while True:
            data += self.sock.recv(1024)
            lines = data.split('\n')
            data = lines.pop()
            for line in lines:
                self.parse_line(line.strip())

    def connect(self):
        self.wait_for_socket()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)

    def start(self):
        thread = threading.Thread(target=self._socket_thread)
        thread.daemon = True
        thread.start()
