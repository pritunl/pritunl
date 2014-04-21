from constants import *
from exceptions import *
from pritunl import app_server
from server import Server
from organization import Organization
from event import Event
from log_entry import LogEntry
from cache import cache_db
import httplib
import logging
import os
import json
import utils
import threading
import time
import websocket

logger = logging.getLogger(APP_NAME)

class NodeServer(Server):
    str_options = Server.str_options | {'node_host', 'node_key'}
    int_options = Server.int_options | {'node_port'}
    default_options = dict(Server.default_options.items() + {
        'node_port': 9800,
    }.items())
    type = NODE_SERVER

    def dict(self):
        server_dict = Server.dict(self)
        server_dict.update({
            'node_host': self.node_host,
            'node_port': self.node_port,
            'node_key': self.node_key,
        })
        return server_dict

    def _initialize(self):
        Server._initialize(self)
        with open(os.path.join(self.path, NODE_SERVER), 'w'):
            pass

    def _request(self, method, endpoint='', json_data=None):
        return getattr(utils.request, method)(
            self._get_node_url(endpoint=endpoint),
            timeout=HTTP_REQUEST_TIMEOUT,
            headers={
                'API-Key': self.node_key,
            },
            json_data=json_data,
        )

    def _get_node_url(self, scheme='https', endpoint=''):
        return '%s://%s:%s/server/%s%s' % (
            scheme, self.node_host, self.node_port, self.id, endpoint)

    def _com_on_message(self, ws, message):
        responses = []
        for call in json.loads(message):
            try:
                responses.append({
                    'id': call['id'],
                    'response': getattr(self, call['command'])(
                        *call['args']),
                })
            except:
                logger.exception('Node server com thread call ' + \
                    'failed. %s' % {
                        'server_id': self.id,
                        'call_id': call['id'],
                        'call_command': call['command'],
                        'call_args': call['args'],
                    })
        ws.send(json.dumps(responses))

    def _com_on_error(self, ws, error):
        if isinstance(error, websocket.WebSocketConnectionClosedException) or \
                not isinstance(error, websocket.WebSocketException):
            return
        logger.exception('Error with node server ' + \
            'connection occurred. %r' % {
                'server_id': self.id,
                'error': error.message,
            })
        LogEntry(message='Error with node server ' + \
            'connection occurred "%s".' % self.name)

    def _start_server_threads(self):
        self._state = True
        self._ws = None

        def com_thread():
            ws = websocket.WebSocketApp(
                self._get_node_url('wss', '/com'),
                header=['API-Key: %s' % self.node_key],
                on_message=self._com_on_message,
                on_error=self._com_on_error,
            )
            self._ws = ws
            ws.run_forever(ping_interval=SOCKET_PING_INTERVAL,
                timeout=SOCKET_TIMEOUT)
            self.status = False
            self.publish('stopped')
            self.update_clients({}, force=True)

            if self._state:
                LogEntry(message='Node server stopped unexpectedly "%s".' % (
                    self.name))
                Event(type=SERVERS_UPDATED)

        def sub_thread():
            for message in cache_db.subscribe(self.get_cache_key()):
                try:
                    if message == 'stop':
                        self._state = False
                        if self._ws:
                            self._ws.close()
                    elif message == 'stopped':
                        break
                except OSError:
                    pass

        thread = threading.Thread(target=com_thread)
        thread.daemon = True
        thread.start()
        thread = threading.Thread(target=sub_thread)
        thread.daemon = True
        thread.start()

    def tls_verify(self, org_id, user_id):
        org = self.get_org(org_id)
        if not org:
            LogEntry(message='User failed authentication, ' +
                'invalid organization "%s".' % server.name)
            return False
        user = org.get_user(user_id)
        if not user:
            LogEntry(message='User failed authentication, ' +
                'invalid user "%s".' % server.name)
            return False
        return True

    def otp_verify(self, org_id, user_id, otp_code):
        org = self.get_org(org_id)
        if not org:
            LogEntry(message='User failed authentication, ' +
                'invalid organization "%s".' % server.name)
            return False
        user = org.get_user(user_id)
        if not user:
            LogEntry(message='User failed authentication, ' +
                'invalid user "%s".' % server.name)
            return False
        if not user.verify_otp_code(otp_code):
            LogEntry(message='User failed two-step authentication "%s".' % (
                user.name))
            return False
        return True

    def client_connect(self, org_id, user_id):
        org = self.get_org(org_id)
        if not org:
            LogEntry(message='User failed authentication, ' +
                'invalid organization "%s".' % server.name)
            return
        user = org.get_user(user_id)
        if not user:
            LogEntry(message='User failed authentication, ' +
                'invalid user "%s".' % server.name)
            return
        return

    def client_disconnect(self, org_id, user_id):
        org = self.get_org(org_id)
        if not org:
            LogEntry(message='User failed authentication, ' +
                'invalid organization "%s".' % server.name)
            return
        user = org.get_user(user_id)
        if not user:
            LogEntry(message='User failed authentication, ' +
                'invalid user "%s".' % server.name)
            return
        return

    def _generate_ovpn_conf(self):
        if not self.org_count:
            raise ServerMissingOrg('Ovpn conf cannot be generated without ' + \
                'any organizations', {
                    'server_id': self.id,
                })

        logger.debug('Generating node server ovpn conf. %r' % {
            'server_id': self.id,
        })

        if not self.primary_organization or not self.primary_user:
            self._create_primary_user()

        if not os.path.isfile(self.dh_param_path):
            self._generate_dh_param()

        primary_org = Organization.get_org(id=self.primary_organization)
        if not primary_org:
            self._create_primary_user()
        primary_org = Organization.get_org(id=self.primary_organization)

        primary_user = primary_org.get_user(self.primary_user)
        if not primary_user:
            self._create_primary_user()
        primary_user = primary_org.get_user(self.primary_user)

        self.generate_ca_cert()

        push = ''
        if self.mode == LOCAL_TRAFFIC:
            for network in self.local_networks:
                push += 'push "route %s %s"\n' % self._parse_network(network)
        elif self.mode == VPN_TRAFFIC:
            pass
        else:
            push += 'push "redirect-gateway"\n'
        for dns_server in self.dns_servers:
            push += 'push "dhcp-option DNS %s"\n' % dns_server
        push = push.rstrip()

        server_conf = OVPN_INLINE_SERVER_CONF % (
            self.port,
            self.protocol,
            self.interface,
            '%s',
            '%s',
            '%s',
            '%s %s' % self._parse_network(self.network),
            push,
            '120' if self.otp_auth else '60',
            '%s',
            4 if self.debug else 1,
            8 if self.debug else 3,
        )

        if self.otp_auth:
            server_conf += 'auth-user-pass-verify ' + \
                '<%= user_pass_verify_path %> via-file\n'

        if self.lzo_compression:
            server_conf += 'comp-lzo\npush "comp-lzo"\n'

        if self.local_networks:
            server_conf += 'client-to-client\n'

        server_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
            self.ca_cert_path)
        server_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
            primary_user.cert_path)
        server_conf += '<key>\n%s\n</key>\n' % open(
            primary_user.key_path).read().strip()
        server_conf += '<dh>\n%s\n</dh>\n' % open(
            self.dh_param_path).read().strip()

        return server_conf

    def start(self, silent=False):
        cache_db.lock_acquire(self.get_cache_key('op_lock'))
        try:
            if self.status:
                return
            if not self.org_count:
                raise ServerMissingOrg('Server cannot be started without ' + \
                    'any organizations', {
                        'server_id': self.id,
                    })

            logger.debug('Starting node server. %r' % {
                'server_id': self.id,
            })
            ovpn_conf = self._generate_ovpn_conf()

            try:
                response = self._request('post', json_data={
                    'interface': self.interface,
                    'network': self.network,
                    'local_networks': self.local_networks,
                    'ovpn_conf': ovpn_conf,
                    'server_ver': NODE_SERVER_VER,
                })
            except httplib.HTTPException:
                raise NodeConnectionError('Failed to connect to node server', {
                    'server_id': self.id,
                })

            if response.status_code == 401:
                raise InvalidNodeAPIKey('Invalid node server api key', {
                    'server_id': self.id,
                    'status_code': response.status_code,
                    'reason': response.reason,
                })
            elif response.status_code != 200:
                raise ServerStartError('Failed to start node server', {
                    'server_id': self.id,
                    'status_code': response.status_code,
                    'reason': response.reason,
                })

            cache_db.dict_set(self.get_cache_key(), 'start_time',
                str(int(time.time() - 1)))
            self.clear_output()
            self._interrupt = False
            self.status = True
            self._start_server_threads()

            if not silent:
                Event(type=SERVERS_UPDATED)
                LogEntry(message='Started server "%s".' % self.name)
        finally:
            cache_db.lock_release(self.get_cache_key('op_lock'))

    def stop(self, silent=False):
        cache_db.lock_acquire(self.get_cache_key('op_lock'))
        try:
            if not self.status:
                return

            stopped = False
            self.publish('stop')
            for message in cache_db.subscribe(self.get_cache_key(),
                    SUB_RESPONSE_TIMEOUT):
                if message == 'stopped':
                    stopped = True
                    break
            if not stopped:
                raise ServerStopError('Server thread failed to return ' + \
                    'stop event', {
                        'server_id': self.id,
                    })

            if not silent:
                Event(type=SERVERS_UPDATED)
                LogEntry(message='Stopped server "%s".' % self.name)
        finally:
            cache_db.lock_release(self.get_cache_key('op_lock'))

    def force_stop(self, silent=False):
        self.stop(silent)
