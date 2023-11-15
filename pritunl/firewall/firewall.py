from pritunl import callbacks
from pritunl import docdb
from pritunl import utils
from pritunl import logger
from pritunl import iptables

import threading
import time

_clients = docdb.DocDb(
    'instance_id',
    'client_id',
    'address',
)
_lock = threading.Lock()

def _insert_rule(rule, ipv6=False):
    iptables.lock_acquire()
    try:
        for i in range(3):
            try:
                utils.Process(
                    ['ip6tables' if ipv6 else 'iptables', '-I'] + rule,
                ).run(15)
                break
            except:
                if i == 2:
                    raise
                logger.error(
                    'Failed to insert iptables rule, retrying...',
                    'firewalll',
                    rule=rule,
                )
            time.sleep(0.5)
    finally:
        iptables.lock_release()

def _remove_rule(rule, ipv6=False):
    iptables.lock_acquire()
    try:
        for i in range(3):
            try:
                utils.Process(
                    ['ip6tables' if ipv6 else 'iptables', '-D'] + rule,
                ).run(15)
                break
            except:
                if i == 2:
                    raise
                logger.error(
                    'Failed to remove iptables rule, retrying...',
                    'firewalll',
                    rule=rule,
                )
            time.sleep(0.5)
    finally:
        iptables.lock_release()

def _set_name(instance_id):
    return '%s_df' % instance_id

def _set_name6(instance_id):
    return '%s_df6' % instance_id

def update():
    _lock.acquire()
    try:
        all_clients = _clients.find_all()
    finally:
        _lock.release()

    for doc in all_clients:
        if not callbacks.on_firewall_check(
                doc['instance_id'], doc['client_id']):
            close_client(doc['instance_id'], doc['client_id'])

def open_server(server_id, instance_id, port, proto, wg_port):
    utils.check_output_logged(
        ['ipset', 'create', _set_name(instance_id),
            'hash:net', 'family', 'inet'],
    )
    utils.check_output_logged(
        ['ipset', 'create', _set_name6(instance_id),
            'hash:net', 'family', 'inet6'],
    )
    _insert_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-j', 'DROP',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ])
    _insert_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-m', 'set',
        '--match-set', _set_name(instance_id), 'src',
        '-j', 'ACCEPT',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ])
    _insert_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-j', 'DROP',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ], True)
    _insert_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-m', 'set',
        '--match-set', _set_name6(instance_id), 'src',
        '-j', 'ACCEPT',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ], True)
    if wg_port:
        _insert_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-j', 'DROP',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ])
        _insert_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-m', 'set',
            '--match-set', _set_name(instance_id), 'src',
            '-j', 'ACCEPT',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ])
        _insert_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-j', 'DROP',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ], True)
        _insert_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-m', 'set',
            '--match-set', _set_name6(instance_id), 'src',
            '-j', 'ACCEPT',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ], True)

def close_server(server_id, instance_id, port, proto, wg_port):
    _remove_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-j', 'DROP',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ])
    _remove_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-m', 'set',
        '--match-set', _set_name(instance_id), 'src',
        '-j', 'ACCEPT',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ])
    _remove_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-j', 'DROP',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ], True)
    _remove_rule([
        'INPUT',
        '-p', proto,
        '-m', proto,
        '--dport', '%s' % port,
        '-m', 'set',
        '--match-set', _set_name6(instance_id), 'src',
        '-j', 'ACCEPT',
        '-m', 'comment',
        '--comment', 'pritunl-%s' % server_id,
    ], True)
    if wg_port:
        _remove_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-j', 'DROP',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ])
        _remove_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-m', 'set',
            '--match-set', _set_name(instance_id), 'src',
            '-j', 'ACCEPT',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ])
        _remove_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-j', 'DROP',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ], True)
        _remove_rule([
            'INPUT',
            '-p', 'udp',
            '-m', 'udp',
            '--dport', '%s' % wg_port,
            '-m', 'set',
            '--match-set', _set_name6(instance_id), 'src',
            '-j', 'ACCEPT',
            '-m', 'comment',
            '--comment', 'pritunl-%s' % server_id,
        ], True)

    _lock.acquire()
    try:
        utils.check_output_logged(
            ['ipset', 'destroy', _set_name(instance_id)],
        )
        utils.check_output_logged(
            ['ipset', 'destroy', _set_name6(instance_id)],
        )

        _clients.remove({
            'instance_id': instance_id,
        })
    finally:
        _lock.release()

def open_client(instance_id, client_id, addresses):
    for address in addresses:
        if ':' in address:
            name = _set_name6(instance_id)
        else:
            name = _set_name(instance_id)

        _lock.acquire()
        try:
            doc = _clients.insert({
                'instance_id': instance_id,
                'client_id': client_id,
                'address': address,
            })

            count = _clients.count({
                'instance_id': instance_id,
                'address': address,
            })
        finally:
            _lock.release()

        if count == 1:
            try:
                utils.check_output_logged(
                    ['ipset', 'add', name, address],
                )
            except:
                try:
                    utils.check_output_logged(
                        ['ipset', 'del', name, address],
                    )
                except:
                    pass

                _lock.acquire()
                try:
                    _clients.remove_id(doc['id'])
                finally:
                    _lock.release()

                raise

def close_client(instance_id, client_id):
    docs = _clients.find({
        'instance_id': instance_id,
        'client_id': client_id,
    })

    for doc in docs:
        address = doc['address']
        if ':' in address:
            name = _set_name6(instance_id)
        else:
            name = _set_name(instance_id)

        _lock.acquire()
        try:
            _clients.remove_id(doc['id'])

            count = _clients.count({
                'instance_id': instance_id,
                'address': address,
            })
        finally:
            _lock.release()

        if count == 0:
            try:
                utils.check_output_logged(
                    ['ipset', 'del', name, address],
                )
            except:
                _lock.acquire()
                try:
                    _clients.insert(doc)
                finally:
                    _lock.release()

                raise
