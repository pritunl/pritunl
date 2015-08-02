from pritunl.constants import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import mongo
from pritunl import limiter
from pritunl import logger
from pritunl import ipaddress
from pritunl import settings
from pritunl import event

import datetime
import collections
import bson
import hashlib

_limiter = limiter.Limiter('vpn', 'peer_limit', 'peer_limit_timeout')

class Clients(object):
    def __init__(self, server, instance, instance_com):
        self.server = server
        self.instance = instance
        self.instance_com = instance_com

        self.clients = collections.deque()
        self.client_count = 0
        self.ips = {}
        self.dyn_ips = set()
        self.devices = collections.defaultdict(dict)

        self.ip_pool = []
        self.ip_network = ipaddress.IPv4Network(self.server.network)
        for ip_addr in self.ip_network.iterhosts():
            self.ip_pool.append(ip_addr)

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('clients')

    def generate_client_conf(self, user):
        from pritunl.server.utils import get_by_id

        client_conf = ''

        if user.link_server_id:
            link_usr_svr = get_by_id(user.link_server_id,
                fields=('_id', 'network', 'local_networks'))

            client_conf += 'iroute %s %s\n' % utils.parse_network(
                link_usr_svr.network)
            for local_network in link_usr_svr.local_networks:
                client_conf += 'iroute %s %s\n' % utils.parse_network(
                    local_network)
        else:
            if self.server.mode == ALL_TRAFFIC:
                client_conf += 'push "redirect-gateway"\n'

            for dns_server in self.server.dns_servers:
                client_conf += 'push "dhcp-option DNS %s"\n' % dns_server
            if self.server.search_domain:
                client_conf += 'push "dhcp-option DOMAIN %s"\n' % (
                    self.server.search_domain)

            client_conf += 'push "ip-win32 dynamic 0 3600"\n'

            for link_svr in self.server.iter_links(fields=(
                '_id', 'network', 'local_networks')):
                client_conf += 'push "route %s %s"\n' % utils.parse_network(
                    link_svr.network)
                for local_network in link_svr.local_networks:
                    client_conf += 'push "route %s %s"\n' % (
                        utils.parse_network(local_network))

        return client_conf

    def connect(self, client):
        try:
            client_id = client['client_id']
            org_id = utils.ObjectId(client['org_id'])
            user_id = utils.ObjectId(client['user_id'])
            device_id = client.get('device_id')
            device_name = client.get('device_name')
            platform = client.get('platform')
            mac_addr = client.get('mac_addr')
            otp_code = client.get('otp_code')
            remote_ip = client.get('remote_ip')
            devices = self.devices[user_id]

            if not _limiter.validate(remote_ip):
                self.instance_com.send_client_deny(
                    client, 'Too many connect requests')
                return

            org = self.server.get_org(org_id, fields=['_id', 'name'])
            if not org:
                self.instance_com.send_client_deny(
                    client, 'Organization is not valid')
                return

            user = org.get_user(user_id, fields=('_id', 'name', 'email',
                'type', 'auth_type', 'disabled', 'otp_secret',
                'link_server_id'))
            if not user:
                self.instance_com.send_client_deny(client, 'User is not valid')
                return

            if user.disabled:
                logger.LogEntry(message='User failed authentication, ' +
                    'disabled user "%s".' % (user.name))
                self.instance_com.send_client_deny(client, 'User is disabled')
                return

            if not user.auth_check():
                logger.LogEntry(message='User failed authentication, ' +
                    'Google authentication failed "%s".' % (user.name))
                self.instance_com.send_client_deny(
                    client, 'User failed authentication')
                return

            if self.server.otp_auth and  user.type == CERT_CLIENT and \
                not user.verify_otp_code(otp_code, remote_ip):
                logger.LogEntry(message='User failed two-step ' +
                    'authentication "%s".' % user.name)
                self.instance_com.send_client_deny(client, 'Invalid OTP code')
                return

            client_conf = self.generate_client_conf(user)

            if not self.server.multi_device:
                virt_address = self.server.get_ip_addr(org.id, user_id)

                if virt_address and virt_address in self.ips:
                    for cid, device in devices.items():
                        if device['virt_address'] == virt_address:
                            self.instance_com.client_kill(device)
            else:
                virt_address = None
                if devices and device_id:
                    for cid, device in devices.items():
                        if device['device_id'] == device_id:
                            self.instance_com.client_kill(device)

                if not virt_address:
                    virt_address = self.server.get_ip_addr(org.id, user_id)

                if virt_address and virt_address in self.ips:
                    virt_address = None

            if not virt_address:
                while True:
                    try:
                        ip_addr = self.ip_pool.pop()
                    except IndexError:
                        break

                    ip_addr = '%s/%s' % (
                        ip_addr, self.ip_network.prefixlen)

                    if ip_addr not in self.ips:
                        virt_address = ip_addr
                        self.dyn_ips.add(virt_address)
                        break

            if virt_address:
                self.ips[virt_address] = client_id
                devices[client_id] = {
                    'user': user.name,
                    'user_id': user_id,
                    'org': org.name,
                    'org_id': org_id,
                    'client_id': client_id,
                    'device_id': device_id,
                    'device_name': device_name,
                    'type': user.type,
                    'platform': platform,
                    'mac_addr': mac_addr,
                    'virt_address': virt_address,
                    'real_address': remote_ip,
                }
                client_conf += 'ifconfig-push %s %s\n' % utils.parse_network(
                    virt_address)

                if self.server.debug:
                    self.instance_com.push_output('Client conf %s:' % user_id)
                    for conf_line in client_conf.split('\n'):
                        if conf_line:
                            self.instance_com.push_output('  ' + conf_line)

                self.instance_com.send_client_auth(client, client_conf)
            else:
                self.instance_com.send_client_deny(
                    client, 'Unable to assign ip address')
        except:
            logger.exception('Error parsing client connect', 'server',
                server_id=self.server.id,
            )
            self.instance_com.send_client_deny(
                client, 'Error parsing client connect')

    def connected(self, client):
        client_id = client['client_id']
        user_id = utils.ObjectId(client['user_id'])
        org_id = utils.ObjectId(client['org_id'])
        device = self.devices[user_id].get(client_id)

        if not device:
            self.instance_com.push_output(
                'ERROR Unknown client connected org_id=%s user_id=%s' % (
                    org_id, user_id))
            return

        domain = device['user'] + '.' + device['org']
        timestamp = utils.now()

        domain_hash = hashlib.md5()
        domain_hash.update(domain)
        domain_hash = bson.binary.Binary(domain_hash.digest(),
            subtype=bson.binary.MD5_SUBTYPE)

        try:
            id = self.collection.insert({
                'user_id': user_id,
                'server_id': self.server.id,
                'domain': domain_hash,
                'timestamp': timestamp,
                'platform': device['platform'],
                'type': device['type'],
                'device_name': device['device_name'],
                'mac_addr': device['mac_addr'],
                'network': self.server.network,
                'real_address': device['real_address'],
                'virt_address': device['virt_address'],
                'connected_since': int(timestamp.strftime('%s')),
            })
        except:
            logger.exception('Error adding client', 'server',
                server_id=self.server.id,
            )
            self.instance_com.client_kill(device)
            return

        device['id'] = id

        self.clients.append({
            'id': id,
            'client_id': client_id,
            'user_id': user_id,
            'org_id': org_id,
            'virt_address': device['virt_address'],
            'timestamp': timestamp,
        })

        self.instance_com.push_output('User connected org_id=%s user_id=%s' % (
            org_id, user_id))
        self.send_event()

    def disconnected(self, client):
        client_id = client.get('client_id')
        user_id = client.get('user_id')
        user_id = utils.ObjectId(user_id) if user_id else None
        org_id = client.get('org_id')
        org_id = utils.ObjectId(org_id) if org_id else None

        devices = self.devices[user_id]
        device = devices.get(client_id)
        devices.pop(client_id, None)

        if device:
            virt_address = device['virt_address']
            if self.ips.get(virt_address) == client_id:
                self.ips.pop(virt_address, None)

            if virt_address in self.dyn_ips:
                try:
                    self.dyn_ips.remove(virt_address)
                except KeyError:
                    pass
                self.ip_pool.append(virt_address.split('/')[0])

            id = device.get('id')
            if id:
                try:
                    self.collection.remove({
                        '_id': id,
                    })
                except:
                    logger.exception('Error removing client', 'server',
                        server_id=self.server.id,
                    )

        self.instance_com.push_output(
            'User disconnected org_id=%s user_id=%s' % (org_id, user_id))
        self.send_event()

    def disconnect_user(self, user_id):
        devices = self.devices.get(user_id)
        if not devices:
            return

        for device in devices:
            if self.instance.sock_interrupt:
                return
            self.instance_com.client_kill(device)

    def send_event(self):
        for org_id in self.server.organizations:
            event.Event(type=USERS_UPDATED, resource_id=org_id)
        event.Event(type=HOSTS_UPDATED, resource_id=settings.local.host_id)
        event.Event(type=SERVERS_UPDATED)
        self.client_count = len(self.clients)

    @interrupter
    def ping_thread(self):
        try:
            while True:
                try:
                    try:
                        client = self.clients.popleft()
                    except IndexError:
                        yield interrupter_sleep(settings.vpn.client_ttl - 60)
                        if self.instance.sock_interrupt:
                            return
                        continue

                    diff = datetime.timedelta(
                        seconds=settings.vpn.client_ttl - 60) - \
                           (utils.now() - client['timestamp'])

                    if diff.seconds > 1:
                        yield interrupter_sleep(diff.seconds)
                        if self.instance.sock_interrupt:
                            return

                    ip_client_id = self.ips.get(client['virt_address'])
                    if not ip_client_id or ip_client_id != client['client_id']:
                        continue

                    try:
                        timestamp = utils.now()

                        response = self.collection.update({
                            '_id': client['id'],
                        }, {
                            '$set': {
                                'timestamp': timestamp,
                            },
                        })
                        if not response['updatedExisting']:
                            self.instance_com.client_kill(client)
                            continue

                        client['timestamp'] = timestamp
                    except:
                        self.clients.append(client)
                        logger.exception('Failed to update client', 'server',
                            server_id=self.server.id,
                            instance_id=self.instance.id,
                        )
                        continue

                    self.clients.append(client)

                    yield
                    if self.instance.sock_interrupt:
                        return
                except GeneratorExit:
                    raise
                except:
                    logger.exception('Error in client thread', 'server',
                        server_id=self.server.id,
                        instance_id=self.instance.id,
                    )
                    yield interrupter_sleep(3)
                    if self.instance.sock_interrupt:
                        return
        finally:
            client_ids = []
            for _, client in enumerate(self.clients):
                client_ids.append(client['id'])

            try:
                self.collection.remove({
                    '_id': {'$in': client_ids},
                })
            except:
                logger.exception('Error removing client', 'server',
                    server_id=self.server.id,
                )
