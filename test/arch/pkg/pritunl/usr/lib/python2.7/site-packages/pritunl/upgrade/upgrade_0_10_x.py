from pritunl.upgrade.utils import get_collection

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import utils
from pritunl import ipaddress
from pritunl import logger

import os
import sys
import json
import pymongo
import bson
import datetime

def _upgrade_auth():
    username = None
    password = None
    administrators_db = get_collection('administrators')

    db_path = settings.conf.db_path
    if db_path and os.path.exists(db_path):
        with open(db_path, 'r') as db_file:
            db_data = json.loads(db_file.read())

        for key, _, _, value in db_data['data']:
            if key == 'auth':
                username = value.get('username')
                password = value.get('password')
    else:
        logger.warning('No db file found in upgraded', 'upgrade',
            path=db_path,
        )

    if username and password:
        update_doc = {
            'username': username,
            'password': password,
            'token': utils.generate_secret(),
            'secret': utils.generate_secret(),
            'default': False,
            'sessions': [],
        }

        doc = administrators_db.find_one()
        if doc:
            spec = {
                '_id': doc['_id'],
            }
        else:
            spec = {
                'username': username,
            }

        administrators_db.update(spec, update_doc, upsert=True)
    else:
        logger.warning('Username and password not upgraded', 'upgrade',
            path=db_path,
        )

def _upgrade_org_users(org_id, org_path):
    users_db = get_collection('users')
    users_path = os.path.join(org_path, 'users')

    for user_conf_name in os.listdir(users_path):
        user_id = os.path.splitext(user_conf_name)[0]
        user_conf_path = os.path.join(users_path, user_conf_name)
        user_cert_path = os.path.join(org_path, 'certs', user_id + '.crt')
        user_key_path = os.path.join(org_path, 'keys', user_id + '.key')

        if user_id == 'ca':
            spec = {
                'org_id': utils.ObjectId(org_id),
                'type': 'ca',
            }
        else:
            spec = {
                '_id': utils.ObjectId(user_id),
            }

        update_doc = {
            'private_key': None,
            'otp_secret': None,
            'name': None,
            'certificate': None,
            'resource_id': None,
            'org_id': utils.ObjectId(org_id),
            'disabled': False,
            'type': CERT_CLIENT,
            'email': None,
        }

        with open(user_conf_path, 'r') as conf_file:
            for line in conf_file.readlines():
                line = line.strip()
                name, value = line.split('=', 1)

                if name in (
                            'name',
                            'email',
                            'otp_secret',
                        ):
                    update_doc[name] = value
                elif name == 'type':
                    if value == 'client':
                        update_doc['type'] = CERT_CLIENT
                    elif value == 'server':
                        update_doc['type'] = CERT_SERVER
                    elif value == 'client_pool':
                        update_doc['type'] = CERT_CLIENT_POOL
                    elif value == 'server_pool':
                        update_doc['type'] = CERT_SERVER_POOL
                    elif value == 'ca':
                        update_doc['type'] = CERT_CA
                elif name == 'disabled' and value == 'true':
                    user_disabled = True

        if not update_doc['otp_secret']:
            update_doc['otp_secret'] = utils.generate_otp_secret()

        with open(user_cert_path, 'r') as vert_file:
            update_doc['certificate'] = vert_file.read().rstrip('\n')

        with open(user_key_path, 'r') as key_file:
            update_doc['private_key'] = key_file.read().rstrip('\n')

        users_db.update(spec, update_doc, upsert=True)

def _upgrade_org(org_id, org_path):
    organizations_db = get_collection('organizations')
    org_conf_path = os.path.join(org_path, 'ca.conf')

    spec = {
        '_id': utils.ObjectId(org_id),
    }

    update_doc = {
        'name': None,
        'type': ORG_DEFAULT,
        'ca_certificate': None,
        'ca_private_key': None,
    }

    with open(org_conf_path, 'r') as conf_file:
        for line in conf_file.readlines():
            line = line.strip()
            name, value = line.split('=', 1)
            if name == 'name':
                update_doc['name'] = value
            elif name == 'pool' and value == 'true':
                update_doc['type'] = ORG_POOL

    org_ca_cert_path = os.path.join(org_path, 'certs', 'ca.crt')
    with open(org_ca_cert_path, 'r') as org_cert_file:
        update_doc['ca_certificate'] = org_cert_file.read().rstrip('\n')

    org_ca_key_path = os.path.join(org_path, 'keys', 'ca.key')
    with open(org_ca_key_path, 'r') as org_key_file:
        update_doc['ca_private_key'] = org_key_file.read().rstrip('\n')

    organizations_db.update(spec, update_doc, upsert=True)

def _upgrade_server(server_id, server_path):
    servers_db = get_collection('servers')
    servers_ip_pool_db = get_collection('servers_ip_pool')
    server_conf_path = os.path.join(server_path, 'server.conf')
    dh_param_path = os.path.join(server_path, 'dh_param.pem')
    ip_pool_path = os.path.join(server_path, 'ip_pool')

    spec = {
        '_id': utils.ObjectId(server_id),
    }

    update_doc = {
        'lzo_compression': ADAPTIVE,
        'dns_servers': [],
        'protocol': None,
        'links': [],
        'primary_organization': None,
        'instances': [],
        'port': None,
        'network': None,
        'dh_params': None,
        'local_networks': [],
        'primary_user': None,
        'status': ONLINE,
        'debug': False,
        'cipher': 'bf128',
        'bind_address': None,
        'organizations': [],
        'start_timestamp': datetime.datetime.fromtimestamp(0),
        'instances_count': 0,
        'name': None,
        'search_domain': None,
        'replica_count': 1,
        'ca_certificate': None,
        'dh_param_bits': None,
        'mode': None,
        'otp_auth': False,
        'jumbo_frames': False,
        'tls_auth': False,
        'tls_auth_key': None,
        'multi_device': False,
        'hosts': [
            settings.local.host_id,
        ],
    }

    with open(server_conf_path, 'r') as conf_file:
        for line in conf_file.readlines():
            line = line.strip()
            name, value = line.split('=', 1)
            if name in (
                        'primary_user',
                        'primary_organization',
                    ):
                update_doc[name] = utils.ObjectId(value)
            if name in (
                        'name',
                        'protocol',
                        'network',
                        'public_address',
                        'search_domain',
                    ):
                update_doc[name] = value
            elif name in (
                        'port',
                        'dh_param_bits',
                    ):
                update_doc[name] = int(value) if value else None
            elif name in (
                        'otp_auth',
                        'debug',
                    ):
                update_doc[name] = True if value == 'true' else False
            elif name in (
                        'organizations',
                        'local_networks',
                        'dns_servers',
                    ):
                update_doc[name] = value.split(',') if value else []
            elif name == 'lzo_compression':
                update_doc[name] = True if value == 'true' else ADAPTIVE
            elif name == 'mode':
                if value == 'all_traffic':
                    update_doc[name] = ALL_TRAFFIC
                elif value == 'local_traffic':
                    update_doc[name] = LOCAL_TRAFFIC
                elif value == 'vpn_traffic':
                    update_doc[name] = VPN_TRAFFIC

    if os.path.exists(dh_param_path):
        with open(dh_param_path, 'r') as dh_param_file:
            update_doc['dh_params'] = dh_param_file.read().strip()

    if os.path.exists(ip_pool_path):
        with open(ip_pool_path, 'r') as ip_pool_file:
            ip_pool_data = json.loads(ip_pool_file.read())

            network = ip_pool_data['network']
            network_prefixlen = network.split('/')[1]

            for key, value in ip_pool_data.iteritems():
                if key == 'network':
                    continue
                org_id, user_id = key.split('-')
                address, _ = value.split('-')
                address_int = int(ipaddress.IPv4Address(address))

                servers_ip_pool_db.update({
                    '_id': address_int,
                }, {
                    '_id': address_int,
                    'server_id': server_id,
                    'user_id': user_id,
                    'org_id': org_id,
                    'network': network,
                    'address': address + '/' + network_prefixlen,
                }, upsert=True)

    servers_db.update(spec, update_doc, upsert=True)

def upgrade_0_10_x():
    _upgrade_auth()

    dir_path = os.path.join(settings.conf.data_path, 'dh_param_pool')
    if os.path.exists(dir_path):
        dh_params_db = get_collection('dh_params')
        has_data = False

        for file_name in os.listdir(dir_path):
            dh_param_bits, id = file_name.split('_')
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, 'r') as file_data:
                dh_params_db.update({
                    '_id': utils.ObjectId(id),
                }, {
                    'dh_param_bits': int(dh_param_bits),
                    'dh_params': file_data.read().rstrip('\n'),
                }, upsert=True)
            has_data = True

        if not has_data:
            logger.warning('DH param pool not upgraded', 'upgrade',
                path=dir_path,
            )
    else:
        logger.warning('No dh_param_pool dir found in upgrade', 'upgrade',
            path=dir_path,
        )

    dir_path = os.path.join(settings.conf.data_path, 'organizations')
    if os.path.exists(dir_path):
        has_data = False

        for org_id in os.listdir(dir_path):
            org_path = os.path.join(dir_path, org_id)
            if os.path.exists(os.path.join(org_path, 'ca.conf')):
                _upgrade_org(org_id, org_path)
                _upgrade_org_users(org_id, org_path)
                has_data = True

        if not has_data:
            logger.warning('Organizations not upgraded', 'upgrade',
                path=dir_path,
            )
    else:
        logger.warning('No organizations dir found in upgrade', 'upgrade',
            path=dir_path,
        )

    dir_path = os.path.join(settings.conf.data_path, 'servers')
    if os.path.exists(dir_path):
        has_data = False

        for server_id in os.listdir(dir_path):
            server_path = os.path.join(dir_path, server_id)
            if os.path.exists(os.path.join(server_path, 'server.conf')):
                _upgrade_server(server_id, server_path)
                has_data = True

        if not has_data:
            logger.warning('Servers not upgraded', 'upgrade',
                path=dir_path,
            )
    else:
        logger.warning('No servers dir found in upgrade', 'upgrade',
            path=dir_path,
        )
