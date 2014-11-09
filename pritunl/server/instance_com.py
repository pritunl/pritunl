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
        self.bytes_lock = threading.Lock()
        self.bytes_recv = 0
        self.bytes_sent = 0
        self.client = None
        self.clients = []
        self.clients_active = 0
        self.client_count = 0
        self.client_bytes = {}
        self.client_devices = collections.defaultdict(list)
        self.client_ips = set()
        self.client_dyn_ips = set()
        self.cur_timestamp = utils.now()
        self.ip_network = ipaddress.IPv4Network(self.server.network)
        self.ip_pool = []
        self.bandwidth_rate = settings.vpn.bandwidth_update_rate
        for ip_addr in self.ip_network.iterhosts():
            self.ip_pool.append(ip_addr)

    def client_kill(self, client):
        self.sock.send('client-kill %s\n' % client['client_id'])
        self.push_output('Disconnecting user org_id=%s user_id=%s' % (
            client['user_id'], client['org_id']))

    def client_connect(self, client):
        from pritunl.server.utils import get_by_id

        try:
            client_id = client['client_id']
            org_id = bson.ObjectId(client['org_id'])
            user_id = bson.ObjectId(client['user_id'])
            device_id = client.get('device_id')
            device_name = client.get('device_name')
            mac_addr = client.get('mac_addr')
            password = client.get('password')
            remote_ip = client.get('remote_ip')
            devices = self.client_devices[user_id]

            org = self.server.get_org(org_id, fields=['_id'])
            if not org:
                self.send_client_deny(client, 'Organization is not valid')
                return

            user = org.get_user(user_id, fields=[
                '_id', 'name', 'type', 'disabled'])
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

            virt_address = None
            if devices and device_id:
                for i, device in enumerate(devices):
                    if device['device_id'] == device_id:
                        virt_address = device['virt_address']

                        self.client_kill(device)
                        if virt_address in self.client_ips:
                            self.client_ips.remove(virt_address)

                        del devices[i]

            if not virt_address:
                virt_address = self.server.get_ip_addr(org.id, user_id)

            if virt_address and virt_address in self.client_ips:
                virt_address = None

            if not virt_address:
                while True:
                    try:
                        ip_addr = self.ip_pool.pop()
                    except IndexError:
                        break
                    ip_addr = '%s/%s' % (ip_addr, self.ip_network.prefixlen)
                    if ip_addr not in self.client_ips:
                        virt_address = ip_addr
                        self.client_dyn_ips.add(virt_address)
                        break

            if virt_address:
                self.client_ips.add(virt_address)
                devices.append({
                    'user_id': user_id,
                    'org_id': org_id,
                    'client_id': client_id,
                    'device_id': device_id,
                    'device_name': device_name,
                    'type': user.type,
                    'mac_addr': mac_addr,
                    'password': password,
                    'virt_address': virt_address,
                    'real_address': remote_ip,
                })
                client_conf += 'ifconfig-push %s %s\n' % utils.parse_network(
                    virt_address)
                self.send_client_auth(client, client_conf)
            else:
                self.send_client_deny(client, 'Unable to assign ip address')
        except:
            logger.exception('Error parsing client connect', 'server',
                server_id=self.server.id,
                instance_id=self.instance.id,
            )
            self.send_client_deny(client, 'Error parsing client connect')

    def client_connected(self, client):
        client_id = client['client_id']
        org_id = bson.ObjectId(client['org_id'])
        user_id = bson.ObjectId(client['user_id'])
        devices = self.client_devices[user_id]
        data = None

        for device in devices:
            if device['client_id'] == client_id:
                data = device
                break

        if not data:
            self.push_output(
                'ERROR Unknown client connected org_id=%s user_id=%s' % (
                    org_id, user_id))
            return

        self.clients.append({
            'id': user_id,
            'client_id': client_id,
            'device_id': data['device_id'],
            'device_name': data['device_name'],
            'type': data['type'],
            'real_address': data['real_address'],
            'virt_address': data['virt_address'],
            'connected_since': int(utils.now().strftime('%s')),
        })

        if data['type'] == CERT_CLIENT:
            self.clients_active += 1

        self.update_clients()

        self.push_output('User connected org_id=%s user_id=%s' % (
            org_id, user_id))

    def client_disconnect(self, client):
        client_id = client['client_id']
        org_id = bson.ObjectId(client['org_id'])
        user_id = bson.ObjectId(client['user_id'])
        user_type = None
        virt_address = None
        devices = self.client_devices[user_id]

        for i, device in enumerate(devices):
            if device['client_id'] == client_id:
                virt_address = device['virt_address']
                del devices[i]
                break

        for i, clt in enumerate(self.clients):
            if clt['client_id'] == client_id:
                user_type = clt['type']
                virt_address = clt['virt_address']
                del self.clients[i]
                break

        if virt_address:
            if virt_address in self.client_ips:
                self.client_ips.remove(virt_address)

            if virt_address in self.client_dyn_ips:
                self.client_dyn_ips.remove(virt_address)
                self.ip_pool.append(virt_address.split('/')[0])

        if user_type == CERT_CLIENT:
            self.clients_active -= 1

        self.update_clients()

        self.push_output('User disconnected org_id=%s user_id=%s' % (
            org_id, user_id))

    def update_clients(self):
        self.server.collection.update({
            '_id': self.server.id,
            'instances.instance_id': self.instance.id,
        }, {'$set': {
            'instances.$.clients': self.clients,
            'instances.$.clients_active': self.clients_active,
        }})

        if self.client_count != len(self.clients):
            for org_id in self.server.organizations:
                event.Event(type=USERS_UPDATED, resource_id=org_id)
            event.Event(type=HOSTS_UPDATED, resource_id=settings.local.host_id)
            event.Event(type=SERVERS_UPDATED)
            self.client_count = len(self.clients)

    def send_client_auth(self, client, client_conf):
        self.sock.send('client-auth %s %s\n%s\nEND\n' % (
            client['client_id'], client['key_id'], client_conf))

    def send_client_deny(self, client, reason):
        self.sock.send('client-deny %s %s "%s"\n' % (
            client['client_id'], client['key_id'], reason))
        self.push_output('ERROR User auth failed "%s"' % reason)

    def push_output(self, message):
        timestamp = datetime.datetime.utcnow().strftime(
            '%a %b  %d %H:%M:%S %Y').replace('  0', '   ', 1).replace(
            '  ', ' ', 1)
        self.server.output.push_output('%s %s' % (timestamp, message))

    def parse_bytecount(self, client_id, bytes_recv, bytes_sent):
        _, bytes_recv_prev, bytes_sent_prev = self.client_bytes.get(
            client_id, (None, 0, 0))

        self.client_bytes[client_id] = (
            self.cur_timestamp, bytes_recv, bytes_sent)

        self.bytes_lock.acquire()
        self.bytes_recv += bytes_recv - bytes_recv_prev
        self.bytes_sent += bytes_sent - bytes_sent_prev
        self.bytes_lock.release()

    def parse_line(self, line):
        line_14 = line[:14]
        line_18 = line[:18]

        if self.client:
            if line == '>CLIENT:ENV,END':
                cmd = self.client['cmd']
                if cmd == 'connect':
                    self.client_connect(self.client)
                elif cmd == 'connected':
                    self.client_connected(self.client)
                elif cmd == 'disconnected':
                    self.client_disconnect(self.client)
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
                elif env_key == 'IV_HWADDR':
                    self.client['mac_addr'] = env_val
                elif env_key == 'untrusted_ip':
                    self.client['remote_ip'] = env_val
                elif env_key == 'UV_ID':
                    self.client['device_id'] = env_val
                elif env_key == 'UV_NAME':
                    self.client['device_name'] = env_val
                elif env_key == 'password':
                    self.client['password'] = env_val
        elif line_14 == '>BYTECOUNT_CLI':
            client_id, bytes_recv, bytes_sent = line.split(',')
            client_id = client_id.split(':')[1]
            self.parse_bytecount(client_id, int(bytes_recv), int(bytes_sent))
        elif line_14 in ('>CLIENT:CONNEC', '>CLIENT:REAUTH'):
            _, client_id, key_id = line.split(',')
            self.client = {
                'cmd': 'connect',
                'client_id': client_id,
                'key_id': key_id,
            }
        elif line_18 == '>CLIENT:ESTABLISHE':
            _, client_id = line.split(',')
            self.client = {
                'cmd': 'connected',
                'client_id': client_id,
            }
        elif line_18 == '>CLIENT:DISCONNECT':
            _, client_id = line.split(',')
            self.client = {
                'cmd': 'disconnected',
                'client_id': client_id,
            }

    def wait_for_socket(self):
        for _ in xrange(10000):
            if os.path.exists(self.socket_path):
                return
            time.sleep(0.001)
        logger.error('Server management socket path not found', 'server',
            server_id=self.server.id,
            instance_id=self.instance.id,
            socket_path=self.socket_path,
        )

    @interrupter
    def _watch_thread(self):
        try:
            while True:
                self.cur_timestamp = utils.now()
                timestamp_ttl = self.cur_timestamp - datetime.timedelta(
                    seconds=180)

                for client_id, (timestamp, _, _) in self.client_bytes.items():
                    if timestamp < timestamp_ttl:
                        self.client_bytes.pop(client_id, None)

                self.bytes_lock.acquire()
                bytes_recv = self.bytes_recv
                bytes_sent = self.bytes_sent
                self.bytes_recv = 0
                self.bytes_sent = 0
                self.bytes_lock.release()

                if bytes_recv != 0 or bytes_sent != 0:
                    self.server.bandwidth.add_data(
                        utils.now(), bytes_recv, bytes_sent)

                yield interrupter_sleep(self.bandwidth_rate)
                if self.instance.sock_interrupt:
                    return
        except GeneratorExit:
            raise
        except:
            self.push_output('ERROR Management thread error')
            logger.exception('Error in management watch thread', 'server',
                server_id=self.server.id,
                instance_id=self.instance.id,
            )
            self.instance.stop_process()

    def _socket_thread(self):
        try:
            self.connect()

            time.sleep(1)
            self.sock.send('bytecount %s\n' % self.bandwidth_rate)

            data = ''
            while True:
                data += self.sock.recv(SOCKET_BUFFER)
                if not data:
                    if not self.instance.sock_interrupt and \
                            not check_global_interrupt():
                        self.instance.stop_process()
                        self.push_output(
                            'ERROR Management socket exited unexpectedly')
                        logger.error('Management socket exited unexpectedly')
                    return
                lines = data.split('\n')
                data = lines.pop()
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self.parse_line(line)
                    except:
                        logger.exception('Failed to parse line from vpn com',
                            'server',
                            server_id=self.server.id,
                            instance_id=self.instance.id,
                            line=line,
                        )
        except:
            self.push_output('ERROR Management socket exception')
            logger.exception('Error in management socket thread', 'server',
                server_id=self.server.id,
                instance_id=self.instance.id,
            )
            self.instance.stop_process()

    def connect(self):
        self.wait_for_socket()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)

    def start(self):
        thread = threading.Thread(target=self._socket_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._watch_thread)
        thread.daemon = True
        thread.start()
