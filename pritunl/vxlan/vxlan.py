from pritunl.helpers import *
from pritunl import mongo
from pritunl import settings
from pritunl import logger
from pritunl import utils
from pritunl import messenger

import threading
import random
import pymongo
import subprocess

_vxlans = {}
_vxlan_instances = {}
_loaded = False

class Vxlan(object):
    def __init__(self, vxlan_id, server_id, instance_id, ipv6):
        self.vxlan_id = vxlan_id
        self.vxlan_mac = None
        self.vxlan_addr = None
        self.vxlan_addr6 = None
        self.vxlan_net = settings.vpn.vxlan_net_prefix + str(
            self.vxlan_id) + '.0/24'
        self.vxlan_net6 = utils.net4to6x64(
            settings.vpn.ipv6_prefix,
            self.vxlan_net,
        )
        self.server_id = server_id
        self.instance_id = instance_id
        self.ipv6 = ipv6
        self.host_vxlan_id = None
        self.running = False
        self.running_lock = threading.Lock()
        _vxlans[(self.vxlan_id, self.server_id)] = self
        _vxlan_instances[self.vxlan_id] = self.instance_id

    @cached_static_property
    def vxlan_collection(cls):
        return mongo.get_collection('vxlans')

    @cached_property
    def iface_name(self):
        return settings.vpn.vxlan_iface_prefix + str(self.vxlan_id)

    def start(self):
        global _loaded

        local_iface = settings.local.host.local_iface

        if not _loaded:
            _loaded = True
            try:
                utils.check_call_silent([
                    'modprobe',
                    'vxlan',
                ])
            except subprocess.CalledProcessError:
                pass

        self.remove_iface()

        if not local_iface:
            logger.error('Failed to find local interface for vxlan', 'vxlan',
                vxlan_id=self.vxlan_id,
                server_id=self.server_id,
                host_id=settings.local.host_id,
                local_addr=settings.local.host.local_addr,
            )
            raise ValueError('Failed to find local interface for vxlan')

        utils.check_output_logged([
            'ip',
            'link',
            'add',
            self.iface_name,
            'type',
            'vxlan',
            'id',
            str(settings.vpn.vxlan_id_start + self.vxlan_id),
            'dstport',
            '4789',
            'dev',
            local_iface['interface'],
            'nolearning',
        ], ignore_states=['File exists'])

        self.vxlan_mac = utils.get_interface_mac_address(self.iface_name)
        self._init_host()
        self.vxlan_addr = self.get_host_addr(self.host_vxlan_id)
        if self.ipv6:
            self.vxlan_addr6 = utils.ip4to6x64(
                settings.vpn.ipv6_prefix,
                self.vxlan_net,
                self.vxlan_addr,
            )

        utils.check_output_logged([
            'ip',
            'address',
            'add',
            self.vxlan_addr + '/24',
            'dev',
            self.iface_name,
        ], ignore_states=['File exists'])

        if self.ipv6:
            utils.check_output_logged([
                'ip',
                '-6',
                'address',
                'add',
                self.vxlan_addr6 + '/64',
                'dev',
                self.iface_name,
            ], ignore_states=['File exists'])

        utils.check_output_logged([
            'ip',
            'link',
            'set',
            'up',
            self.iface_name,
        ])

        self._init_hosts()

    def _init_host(self):
        local_addr = settings.local.host.local_addr
        local_addr6 = None
        if self.ipv6:
            local_addr6 = settings.local.host.local_addr6

        doc = self.vxlan_collection.find_and_modify({
            '_id': self.vxlan_id,
            'server_id': self.server_id,
            'hosts.host_dst': {'$nin': [local_addr]},
        }, {'$push': {
            'hosts': {
                'vxlan_mac': self.vxlan_mac,
                'host_dst': local_addr,
                'host_dst6': local_addr6,
            },
        }}, new=True)

        if not doc:
            doc = self.vxlan_collection.find_and_modify({
                '_id': self.vxlan_id,
                'server_id': self.server_id,
                'hosts.host_dst': local_addr,
            }, {'$set': {
                'hosts.$.vxlan_mac': self.vxlan_mac,
                'hosts.$.host_dst': local_addr,
                'hosts.$.host_dst6': local_addr6,
            }}, new=True)

        if doc:
            for host_vxlan_id, data in enumerate(doc['hosts']):
                if data['host_dst'] == local_addr:
                    self.host_vxlan_id = host_vxlan_id + 1

        if not self.host_vxlan_id:
            logger.error('Failed to get host vxlan id', 'vxlan',
                vxlan_id=self.vxlan_id,
                server_id=self.server_id,
                host_id=settings.local.host_id,
                local_addr=local_addr,
                local_addr6=local_addr6,
            )
            raise ValueError('Failed to get host vxlan id')

        messenger.publish('vxlan', {
            'vxlan_id': self.vxlan_id,
            'server_id': self.server_id,
            'host_vxlan_id': self.host_vxlan_id,
            'vxlan_mac': self.vxlan_mac,
            'host_dst': local_addr,
            'host_dst6': local_addr6,
        })

    def _init_hosts(self):
        self.running_lock.acquire()
        try:
            self.running = True
        finally:
            self.running_lock.release()

        doc = self.vxlan_collection.find_one({
            '_id': self.vxlan_id,
            'server_id': self.server_id,
        })

        if not doc:
            logger.error('Lost vxlan doc', 'vxlan',
                vxlan_id=self.vxlan_id,
                server_id=self.server_id,
            )
            return

        for host_vxlan_id, data in enumerate(doc['hosts']):
            host_dst = data.get('host_dst')
            host_dst6 = data.get('host_dst6')
            vxlan_mac = data.get('vxlan_mac')
            if not host_dst or not vxlan_mac:
                continue

            self.add_host(host_vxlan_id + 1, vxlan_mac, host_dst, host_dst6)

    def stop(self):
        if _vxlan_instances.get(self.vxlan_id) != self.instance_id:
            return

        self.running_lock.acquire()
        try:
            self.running = False
        finally:
            self.running_lock.release()

        self.remove_iface()

        _vxlans.pop((self.vxlan_id, self.server_id))

    def remove_iface(self):
        if _vxlan_instances.get(self.vxlan_id) != self.instance_id:
            return

        try:
            utils.check_call_silent([
                'ip',
                'link',
                'set',
                'down',
                self.iface_name,
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_call_silent([
                'ip',
                'link',
                'del',
                self.iface_name,
            ])
        except subprocess.CalledProcessError:
            pass

    def get_host_addr(self, host_vxlan_id):
        return settings.vpn.vxlan_net_prefix + str(
            self.vxlan_id) + '.' + str(host_vxlan_id)

    def get_host_addr6(self, host_vxlan_id):
        return utils.ip4to6x64(
            settings.vpn.ipv6_prefix,
            settings.vpn.vxlan_net_prefix + str(self.vxlan_id) + '.0/24',
            self.get_host_addr(host_vxlan_id),
        )

    def add_host(self, host_vxlan_id, vxlan_mac, host_dst, host_dst6):
        if settings.local.host.local_addr == host_dst:
            return

        self.running_lock.acquire()
        try:
            if not self.running:
                return

            for i in range(2):
                try:
                    if i == 0:
                        check_func = utils.check_output
                    else:
                        check_func = utils.check_output_logged

                    check_func([
                        'bridge',
                        'fdb',
                        'add',
                        vxlan_mac,
                        'dev',
                        self.iface_name,
                        'dst',
                        host_dst,
                    ], ignore_states=['File exists'])

                    break
                except subprocess.CalledProcessError:
                    if i == 0:
                        utils.check_output_logged([
                            'bridge',
                            'fdb',
                            'del',
                            vxlan_mac,
                            'dev',
                            self.iface_name,
                        ])
                    else:
                        raise

            utils.check_output_logged([
                'arp',
                '-s',
                self.get_host_addr(host_vxlan_id),
                vxlan_mac,
            ])

            if host_dst6:
                for i in range(2):
                    try:
                        if i == 0:
                            check_func = utils.check_output
                        else:
                            check_func = utils.check_output_logged

                        check_func([
                            'ip',
                            '-6',
                            'neighbour',
                            'add',
                            self.get_host_addr6(host_vxlan_id),
                            'lladdr',
                            vxlan_mac,
                            'dev',
                            self.iface_name,
                        ], ignore_states=['File exists'])

                        break
                    except subprocess.CalledProcessError:
                        if i == 0:
                            utils.check_output_logged([
                                'ip',
                                '-6',
                                'neighbour',
                                'del',
                                self.get_host_addr6(host_vxlan_id),
                                'dev',
                                self.iface_name,
                            ])
                            for j in range(30):
                                try:
                                    utils.check_call_silent([
                                        'ip',
                                        '-6',
                                        'neighbour',
                                        'del',
                                        self.get_host_addr6(host_vxlan_id),
                                        'dev',
                                        self.iface_name,
                                    ])
                                except:
                                    break
                                time.sleep(0.5)
                        else:
                            raise
        except:
            logger.error('Failed to add vxlan host', 'vxlan',
                vxlan_id=self.vxlan_id,
                server_id=self.server_id,
            )
            raise
        finally:
            self.running_lock.release()

def _get_ids():
    ids = list(range(0, 256))
    random.shuffle(ids)
    return ids

def get_vxlan_id(server_id):
    coll = mongo.get_collection('vxlans')
    vxlan_ids = _get_ids()

    while True:
        doc = coll.find_one({
            'server_id': server_id,
        })
        if doc:
            return doc['_id']

        vxlan_id = vxlan_ids.pop()
        try:
            coll.insert({
                '_id': vxlan_id,
                'server_id': server_id,
                'hosts': [],
            })
        except pymongo.errors.DuplicateKeyError:
            continue

        return vxlan_id

def get_vxlan(server_id, instance_id, ipv6):
    return Vxlan(get_vxlan_id(server_id), server_id, instance_id, ipv6)

def get_vxlan_net(server_id):
    vxlan_id = get_vxlan_id(server_id)
    return settings.vpn.vxlan_net_prefix + str(vxlan_id) + '.0/24'

def get_vxlan_net6(server_id):
    vxlan_id = get_vxlan_id(server_id)
    return utils.net4to6x64(
        settings.vpn.ipv6_prefix,
        vxlan_id,
    )

def on_vxlan(msg):
    vxlan_id = msg['message']['vxlan_id']
    server_id = msg['message']['server_id']
    host_vxlan_id = msg['message']['host_vxlan_id']
    vxlan_mac = msg['message']['vxlan_mac']
    host_dst = msg['message']['host_dst']
    host_dst6 = msg['message'].get('host_dst6')

    vxlan = _vxlans.get((vxlan_id, server_id))
    if not vxlan:
        return

    vxlan.add_host(host_vxlan_id, vxlan_mac, host_dst, host_dst6)
