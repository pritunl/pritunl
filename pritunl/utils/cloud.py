from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings
from pritunl import utils
from pritunl import ipaddress
from pritunl import logger

import requests
import subprocess
import hashlib
import base64
import hmac
import urllib.parse

def pritunl_cloud_get_metadata():
    cloud_host = settings.app.pritunl_cloud_host
    cloud_token = settings.app.pritunl_cloud_token
    cloud_secret = settings.app.pritunl_cloud_secret
    org_id = subprocess.check_output([
        'pci', 'get', '+/instance/self/organization']).decode()
    vpc_id = subprocess.check_output([
        'pci', 'get', '+/vpc/self/id']).decode()
    private_ips = subprocess.check_output([
        'pci', 'get', '+/instance/self/private_ips']).decode()
    private_ip = private_ips.split(',')[0]
    private_ips6 = subprocess.check_output([
        'pci', 'get', '+/instance/self/private_ips6']).decode()
    private_ip6 = private_ips6.split(',')[0]

    if not cloud_host.startswith(('http://', 'https://')):
        cloud_host = 'https://' + cloud_host
    cloud_host = urllib.parse.urlparse(cloud_host).netloc

    insecure = False
    try:
        ipaddress.ip_network(cloud_host)
        insecure = True
    except (ipaddress.AddressValueError, ValueError):
        pass

    return {
        'cloud_host': cloud_host,
        'cloud_token': cloud_token,
        'cloud_secret': cloud_secret,
        'insecure': insecure,
        'org_id': org_id,
        'vpc_id': vpc_id,
        'private_ip': private_ip,
        'private_ip6': private_ip6,
    }

def pritunl_cloud_get_routes(metadata=None):
    if not metadata:
        metadata = pritunl_cloud_get_metadata()

    path = f"/vpc/{metadata['vpc_id']}/routes"
    timestamp = str(int(utils.time_now()))
    nonce = utils.rand_str(32)

    auth_str = "&".join([
        metadata['cloud_token'],
        timestamp,
        nonce,
        "GET",
        path,
    ])

    hash_func = hmac.new(
        metadata['cloud_secret'].encode('utf-8'),
        auth_str.encode('utf-8'),
        hashlib.sha512
    )
    raw_signature = hash_func.digest()
    sig = base64.b64encode(raw_signature).decode('utf-8')

    response = requests.get(
        f"https://{metadata['cloud_host']}{path}",
        headers={
            "Organization": metadata['org_id'],
            "Auth-Token": metadata['cloud_token'],
            "Auth-Timestamp": timestamp,
            "Auth-Nonce": nonce,
            "Auth-Signature": sig,
        },
    )

    if response.status_code != 200:
        logger.error('Pritunl Cloud api error', 'utils',
            status_code=response.status_code,
            response=response.content,
        )
        raise RequestError('Pritunl Cloud api bad status %s' %
            response.status_code)

    return response.json()

def pritunl_cloud_add_route(dest_network, metadata=None):
    if not metadata:
        metadata = pritunl_cloud_get_metadata()

    vpc_routes = pritunl_cloud_get_routes(metadata)

    if ':' in dest_network:
        target = metadata['private_ip6']
    else:
        target = metadata['private_ip']

    exists = False
    updated = False

    for route in vpc_routes:
        if route['destination'] == dest_network:
            exists = True
            if route['target'] != target:
                route['target'] = target
                updated = True

    if not exists:
        vpc_routes.append({
            'destination': dest_network,
            'target': target
        })
        updated = True

    if not updated:
        return

    path = f"/vpc/{metadata['vpc_id']}/routes"
    timestamp = str(int(utils.time_now()))
    nonce = utils.rand_str(32)

    auth_str = "&".join([
        metadata['cloud_token'],
        timestamp,
        nonce,
        "PUT",
        path,
    ])

    hash_func = hmac.new(
        metadata['cloud_secret'].encode('utf-8'),
        auth_str.encode('utf-8'),
        hashlib.sha512
    )
    raw_signature = hash_func.digest()
    sig = base64.b64encode(raw_signature).decode('utf-8')

    response = requests.put(
        f"https://{metadata['cloud_host']}{path}",
        headers={
            "Content-Type": "application/json",
            "Organization": metadata['org_id'],
            "Auth-Token": metadata['cloud_token'],
            "Auth-Timestamp": timestamp,
            "Auth-Nonce": nonce,
            "Auth-Signature": sig,
        },
        json=vpc_routes,
    )

    if response.status_code != 200:
        logger.error('Pritunl Cloud api error', 'utils',
            status_code=response.status_code,
            response=response.content,
        )
        raise RequestError('Pritunl Cloud api bad status %s' %
            response.status_code)
