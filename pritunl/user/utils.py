from pritunl.user.user import User

from pritunl.constants import *

import threading
import re

def new_pooled_user(org, type):
    type = {
        CERT_SERVER: CERT_SERVER_POOL,
        CERT_CLIENT: CERT_CLIENT_POOL,
    }[type]

    thread = threading.Thread(name="PoolNewUser",
        target=org.new_user, kwargs={
            'type': type,
            'block': False,
        },
    )
    thread.daemon = True
    thread.start()

def reserve_pooled_user(org, name=None, email=None, pin=None, type=CERT_CLIENT,
        groups=None, auth_type=None, yubico_id=None, disabled=None,
        resource_id=None, mac_addresses=None, dns_servers=None,
        dns_suffix=None, bypass_secondary=None, client_to_client=None,
        port_forwarding=None):
    doc = {}

    if name is not None:
        doc['name'] = name
    if email is not None:
        doc['email'] = email
    if pin is not None:
        doc['pin'] = pin
    if type is not None:
        doc['type'] = type
    if groups is not None:
        doc['groups'] = groups
    if auth_type is not None:
        doc['auth_type'] = auth_type
    if yubico_id is not None:
        doc['yubico_id'] = yubico_id
    if disabled is not None:
        doc['disabled'] = disabled
    if resource_id is not None:
        doc['resource_id'] = resource_id
    if mac_addresses is not None:
        doc['mac_addresses'] = mac_addresses
    if dns_servers is not None:
        doc['dns_servers'] = dns_servers
    if dns_suffix is not None:
        doc['dns_suffix'] = dns_suffix
    if bypass_secondary is not None:
        doc['bypass_secondary'] = bypass_secondary
    if client_to_client is not None:
        doc['client_to_client'] = client_to_client
    if port_forwarding is not None:
        doc['port_forwarding'] = port_forwarding

    doc = User.collection.find_one_and_update({
        'org_id': org.id,
        'type': {
            CERT_SERVER: CERT_SERVER_POOL,
            CERT_CLIENT: CERT_CLIENT_POOL,
        }[type],
    }, {
        '$set': doc,
    }, return_document=True)

    if doc:
        usr = User(org=org, doc=doc)
        usr.assign_ip_addr()
        return usr

def get_user(org, id, fields=None):
    return User(org=org, id=id, fields=fields)

def find_user(org, name=None, type=None, resource_id=None):
    spec = {
        'org_id': org.id,
    }
    if name is not None:
        spec['name'] = {
            '$regex': '^%s$' % re.escape(name),
            '$options': 'i',
        }
    if type is not None:
        spec['type'] = type
    if resource_id is not None:
        spec['resource_id'] = resource_id
    return User(org, spec=spec)

def find_user_auth(name, auth_type):
    from pritunl import organization

    spec = {
        'name': {
            '$regex': '^%s$' % re.escape(name),
            '$options': 'i',
        },
        'auth_type': auth_type,
    }

    usr = User(None, spec=spec)
    if not usr:
        return None

    usr.org = organization.get_by_id(usr.org_id)
    if not usr.org:
        return None

    return usr

def iter_unreg_devices():
    cursor = User.collection.find({
        'devices.registered': False,
    }).sort('name')

    override = User.is_device_key_override
    for doc in cursor:
        devices = doc.get('devices')
        if not devices:
            continue

        for device in devices:
            if device.get('registered'):
                continue

            yield {
                'id': device.get('id'),
                'org_id': doc.get('org_id'),
                'user_id': doc.get('_id'),
                'user_name': doc.get('name'),
                'name': device.get('name'),
                'platform': device.get('platform'),
                'override': override,
            }
