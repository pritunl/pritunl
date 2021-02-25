from pritunl.server.listener import *

from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import utils
from pritunl import mongo
from pritunl import clients
from pritunl import ipaddress
from pritunl import monitoring

import os
import time
import datetime
import threading
import socket
import uuid
import random
import bson

class ServerInstanceCom(object):
    def __init__(self, svr, instance):
        self.server = svr
        self.instance = instance
        self.sock = None
        self.sock_lock = threading.Lock()
        self.socket_path = instance.management_socket_path
        self.bytes_lock = threading.Lock()
        self.bytes_recv = 0
        self.bytes_sent = 0
        self.client = None
        self.clients = clients.Clients(svr, instance, self)
        self.client_bytes = {}
        self.cur_timestamp = utils.now()
        self.bandwidth_rate = settings.vpn.bandwidth_update_rate

    @cached_static_property
    def users_ip_collection(cls):
        return mongo.get_collection('users_ip')

    def sock_send(self, data):
        self.sock_lock.acquire()
        try:
            self.sock.send(data.encode())
        finally:
            self.sock_lock.release()

    def client_kill(self, client_id):
        self.clients.disconnected(client_id)
        self.sock_send('client-kill %s\n' % client_id)

    def send_client_auth(self, client_id, key_id, client_conf):
        self.sock_send('client-auth %s %s\n%s\nEND\n' % (
            client_id, key_id, client_conf))

    def send_client_deny(self, client_id, key_id, reason, client_reason=None):
        self.sock_send('client-deny %s %s "%s"%s\n' % (client_id, key_id,
            reason, ((' "%s"' % client_reason) if client_reason else '')))
        self.push_output('ERROR User auth failed "%s"' % reason)

    def push_output(self, message):
        self.server.output.push_message(message)

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
        if self.client:
            if line == '>CLIENT:ENV,END':
                cmd = self.client['cmd']
                if cmd == 'connect':
                    self.clients.connect(self.client)
                elif cmd == 'reauth':
                    self.clients.connect(self.client, reauth=True)
                elif cmd == 'connected':
                    self.clients.connected(self.client.get('client_id'))
                elif cmd == 'disconnected':
                    self.clients.disconnected(self.client.get('client_id'))
                self.client = None
            elif line.startswith('>CLIENT:ENV'):
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

                    self.client['org_id'] = utils.ObjectId(org_id)
                    self.client['user_id'] = utils.ObjectId(user_id)
                elif env_key == 'IV_HWADDR':
                    self.client['mac_addr'] = env_val
                elif env_key == 'untrusted_ip':
                    self.client['remote_ip'] = env_val
                elif env_key == 'untrusted_ip6':
                    remote_ip = env_val
                    if remote_ip.startswith('::ffff:'):
                        remote_ip = remote_ip.split(':')[-1]
                    self.client['remote_ip'] = remote_ip
                elif env_key == 'IV_PLAT' and not self.client.get('platform'):
                    if 'chrome' in env_val.lower():
                        env_val = 'chrome'
                        self.client['device_id'] = uuid.uuid4().hex
                        self.client['device_name'] = 'chrome-os'
                    self.client['platform'] = env_val
                elif env_key == 'UV_ID':
                    self.client['device_id'] = env_val
                elif env_key == 'UV_NAME':
                    self.client['device_name'] = env_val
                elif env_key == 'UV_PLATFORM':
                    self.client['platform'] = env_val
                elif env_key == 'username':
                    self.client['username'] = env_val
                elif env_key == 'password':
                    self.client['password'] = env_val
            else:
                self.push_output('CCOM> %s' % line[1:])
        elif line.startswith('>BYTECOUNT_CLI'):
            client_id, bytes_recv, bytes_sent = line.split(',')
            client_id = client_id.split(':')[1]
            self.parse_bytecount(client_id, int(bytes_recv), int(bytes_sent))
        elif line.startswith('>CLIENT:CONNECT'):
            _, client_id, key_id = line.split(',')
            self.client = {
                'cmd': 'connect',
                'client_id': client_id,
                'key_id': key_id,
            }
        elif line.startswith('>CLIENT:REAUTH'):
            _, client_id, key_id = line.split(',')
            self.client = {
                'cmd': 'reauth',
                'client_id': client_id,
                'key_id': key_id,
            }
        elif line.startswith('>CLIENT:ESTABLISHED'):
            _, client_id = line.split(',')
            self.client = {
                'cmd': 'connected',
                'client_id': client_id,
            }
        elif line.startswith('>CLIENT:DISCONNECT'):
            _, client_id = line.split(',')
            self.client = {
                'cmd': 'disconnected',
                'client_id': client_id,
            }
        elif line.startswith('SUCCESS:'):
            self.push_output('COM> %s' % line)

    def wait_for_socket(self):
        for _ in range(10000):
            if os.path.exists(self.socket_path):
                return
            time.sleep(0.001)
            if self.instance.sock_interrupt:
                return

        logger.error('Server management socket path not found', 'server',
            server_id=self.server.id,
            instance_id=self.instance.id,
            socket_path=self.socket_path,
        )

    def on_msg(self, evt):
        msg = evt['message']
        event_type = msg[0]

        if event_type == 'user_disconnect':
            user_id = msg[1]
            self.clients.disconnect_user(user_id)
        elif event_type == 'user_disconnect_id':
            user_id = msg[1]
            client_id = msg[2]
            server_id = None
            if len(msg) > 3:
                server_id = msg[3]
            self.clients.disconnect_user_id(user_id, client_id, server_id)
        elif event_type == 'user_disconnect_mac':
            user_id = msg[1]
            host_id = msg[2]
            mac_addr = msg[3]
            server_id = None
            if len(msg) > 4:
                server_id = msg[4]
            self.clients.disconnect_user_mac(user_id, host_id,
                mac_addr, server_id)
        elif event_type == 'user_reconnect':
            user_id = msg[1]
            host_id = msg[2]
            server_id = None
            if len(msg) > 3:
                server_id = msg[3]
            self.clients.reconnect_user(user_id, host_id, server_id)
        elif event_type == 'route_advertisement':
            server_id = msg[1]
            vpc_region = msg[2]
            vpc_id = msg[3]
            network = msg[4]

            if server_id != self.server.id:
                return

            self.instance.reserve_route_advertisement(
                vpc_region, vpc_id, network)

    @interrupter
    def _watch_thread(self):
        try:
            while True:
                self.cur_timestamp = utils.now()
                timestamp_ttl = self.cur_timestamp - datetime.timedelta(
                    seconds=180)

                for client_id, (timestamp, _, _) in list(
                        self.client_bytes.items()):
                    if timestamp < timestamp_ttl:
                        self.client_bytes.pop(client_id, None)

                self.bytes_lock.acquire()
                bytes_recv = self.bytes_recv
                bytes_sent = self.bytes_sent
                self.bytes_recv = 0
                self.bytes_sent = 0
                self.bytes_lock.release()

                monitoring.insert_point('server_bandwidth', {
                    'host': settings.local.host.name,
                    'server': self.server.name,
                }, {
                    'bytes_sent': bytes_sent,
                    'bytes_recv': bytes_recv,
                })

                monitoring.insert_point('server', {
                    'host': settings.local.host.name,
                    'server': self.server.name,
                }, {
                    'device_count': self.clients.clients.count({}),
                })

                if bytes_recv != 0 or bytes_sent != 0:
                    self.server.bandwidth.add_data(
                        utils.now(), bytes_recv, bytes_sent)

                yield interrupter_sleep(self.bandwidth_rate)
                if self.instance.sock_interrupt:
                    return
        except GeneratorExit:
            raise
        except:
            try:
                self.push_output('ERROR Management rate thread error')
            except:
                pass
            logger.exception('Error in management rate thread', 'server',
                server_id=self.server.id,
                instance_id=self.instance.id,
            )
            self.instance.stop_process()

    def _socket_thread(self):
        try:
            self.connect()
            time.sleep(1)
            self.sock_send('bytecount %s\n' % self.bandwidth_rate)

            add_listener(self.instance.id, self.on_msg)

            data = ''
            while True:
                data += self.sock.recv(SOCKET_BUFFER).decode()
                if not data or self.instance.sock_interrupt:
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
            if not self.instance.sock_interrupt:
                self.push_output('ERROR Management socket exception')
                logger.exception('Error in management socket thread',
                    'server',
                    server_id=self.server.id,
                    instance_id=self.instance.id,
                    socket_path=self.socket_path,
                )
            self.instance.stop_process()
        finally:
            remove_listener(self.instance.id)
            self.clients.stop()

    def _stress_thread(self):
        try:
            i = 0

            for org in self.server.iter_orgs():
                for user in org.iter_users():
                    if user.type != CERT_CLIENT:
                        continue

                    i += 1

                    client = {
                        'client_id': i,
                        'key_id': 1,
                        'org_id': org.id,
                        'user_id': user.id,
                        'mac_addr': utils.rand_str(16),
                        'remote_ip': str(
                            ipaddress.ip_address(100000000 + random.randint(
                                0, 1000000000))),
                        'platform': 'linux',
                        'device_id': str(bson.ObjectId()),
                        'device_name': utils.random_name(),
                    }

                    self.clients.connect(client)
        except:
            logger.exception('Error in stress thread', 'server',
                server_id=self.server.id,
                instance_id=self.instance.id,
                socket_path=self.socket_path,
            )

    def connect(self):
        self.wait_for_socket()

        if self.instance.sock_interrupt:
            return

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)

    def start(self):
        thread = threading.Thread(target=self._socket_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._watch_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self.clients.ping_thread)
        thread.daemon = True
        thread.start()

        self.clients.start()

        if settings.vpn.stress_test:
            thread = threading.Thread(target=self._stress_thread)
            thread.daemon = True
            thread.start()
