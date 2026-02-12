from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings
from pritunl import utils

import requests
import time
import json
import subprocess
import hashlib
import base64
import email.utils
from urllib.parse import urlparse

from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key,
    load_pem_private_key,
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def _sign_request(method, url, mdata, body=None):
    parsed = urlparse(url)
    host = parsed.hostname
    path = parsed.path
    if parsed.query:
        path += '?' + parsed.query

    now = email.utils.formatdate(usegmt=True)
    request_target = '%s %s' % (method.lower(), path)

    headers = {
        'date': now,
        'host': host,
    }

    signing_headers = ['date', '(request-target)', 'host']
    signing_string_parts = [
        'date: %s' % now,
        '(request-target): %s' % request_target,
        'host: %s' % host,
    ]

    if body is not None:
        body_bytes = body.encode() if isinstance(body, str) else body
        body_hash = hashlib.sha256(body_bytes).digest()
        body_b64 = base64.b64encode(body_hash).decode()
        headers['content-type'] = 'application/json'
        headers['content-length'] = str(len(body_bytes))
        headers['x-content-sha256'] = body_b64
        signing_headers.extend([
            'content-type', 'content-length', 'x-content-sha256',
        ])
        signing_string_parts.extend([
            'content-type: application/json',
            'content-length: %s' % len(body_bytes),
            'x-content-sha256: %s' % body_b64,
        ])

    signing_string = '\n'.join(signing_string_parts)

    private_key = load_pem_private_key(
        mdata['private_key'].encode(), password=None,
        backend=default_backend(),
    )

    signature = private_key.sign(
        signing_string.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    b64_sig = base64.b64encode(signature).decode()
    key_id = '%s/%s/%s' % (
        mdata['tenancy_ocid'],
        mdata['user_ocid'],
        mdata['fingerprint'],
    )

    auth_header = (
        'Signature version="1",'
        'headers="%s",'
        'keyId="%s",'
        'algorithm="rsa-sha256",'
        'signature="%s"'
    ) % (' '.join(signing_headers), key_id, b64_sig)

    headers['authorization'] = auth_header
    return headers

def _oci_get(url, mdata):
    headers = _sign_request('GET', url, mdata)
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise RequestError('Oracle API bad status %s: %s' % (
            resp.status_code, resp.text))
    return resp.json()

def _oci_put(url, mdata, data):
    body = json.dumps(data)
    headers = _sign_request('PUT', url, mdata, body=body)
    resp = requests.put(url, headers=headers, data=body)
    if resp.status_code != 200:
        raise RequestError('Oracle API bad status %s: %s' % (
            resp.status_code, resp.text))
    return resp.json()

def oracle_get_metadata():
    public_key_pem = settings.app.oracle_public_key
    private_key_pem = settings.app.oracle_private_key
    public_key = load_pem_public_key(
        public_key_pem.encode(), default_backend())

    fingerprint = utils.unsafe_md5()
    fingerprint.update(public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    fingerprint = fingerprint.hexdigest()
    fingerprint = ':'.join(fingerprint[i:i + 2] for i in range(0, 32, 2))

    output = subprocess.check_output(['oci-metadata', '--json']).decode()
    metadata = json.loads(output)

    return {
        'user_ocid': settings.app.oracle_user_ocid,
        'private_key': private_key_pem,
        'fingerprint': fingerprint,
        'region_name': metadata['instance']['canonicalRegionName'],
        'tenancy_ocid': metadata['instance']['tenantId'],
        'compartment_ocid': metadata['instance']['compartmentId'],
        'vnic_ocid': metadata['vnics'][0]['vnicId'],
    }

def oracle_add_route(dest_network):
    mdata = oracle_get_metadata()
    region = mdata['region_name']
    base_url = 'https://iaas.%s.oraclecloud.com/20160918' % region

    vnic = _oci_get('%s/vnics/%s' % (base_url, mdata['vnic_ocid']), mdata)

    if not vnic.get('skipSourceDestCheck'):
        _oci_put(
            '%s/vnics/%s' % (base_url, mdata['vnic_ocid']),
            mdata,
            {'skipSourceDestCheck': True},
        )
        time.sleep(0.25)

    private_ips = _oci_get(
        '%s/privateIps?vnicId=%s' % (base_url, mdata['vnic_ocid']),
        mdata,
    )

    private_ip_ocid = None
    subnet_ocid = None
    for private_ip in private_ips:
        private_ip_ocid = private_ip['id']
        subnet_ocid = private_ip['subnetId']
        break

    if not private_ip_ocid or not subnet_ocid:
        raise ValueError('Failed to find Oracle vnic ocid info')

    subnet = _oci_get('%s/subnets/%s' % (base_url, subnet_ocid), mdata)
    vcn_ocid = subnet['vcnId']

    tables = _oci_get(
        '%s/routeTables?compartmentId=%s&vcnId=%s' % (
            base_url, mdata['compartment_ocid'], vcn_ocid),
        mdata,
    )

    for table in tables:
        exists = False
        replace = False

        route_rules = []
        for route in table.get('routeRules', []):
            if route.get('cidrBlock') == dest_network:
                exists = True
                if route.get('networkEntityId') != private_ip_ocid:
                    route['networkEntityId'] = private_ip_ocid
                    replace = True
            route_rules.append(route)

        if exists and not replace:
            continue

        if not replace:
            route_rules.append({
                'cidrBlock': dest_network,
                'networkEntityId': private_ip_ocid,
                'destinationType': 'CIDR_BLOCK',
            })

        _oci_put(
            '%s/routeTables/%s' % (base_url, table['id']),
            mdata,
            {'routeRules': route_rules},
        )
