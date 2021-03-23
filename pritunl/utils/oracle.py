from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings

import oci
import requests
import time
import json
import subprocess
import hashlib
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def oracle_get_metadata():
    public_key_pem = settings.app.oracle_public_key
    private_key_pem = settings.app.oracle_private_key
    public_key = load_pem_public_key(
        public_key_pem.encode(), default_backend())

    fingerprint = hashlib.md5()

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
        'tenancy_ocid': metadata['instance']['compartmentId'],
        'compartment_ocid': metadata['instance']['compartmentId'],
        'vnic_ocid': metadata['vnics'][0]['vnicId'],
    }

def oracle_add_route(dest_network):
    mdata = oracle_get_metadata()
    vnet_client = oci.core.virtual_network_client.VirtualNetworkClient({
        'user': mdata['user_ocid'],
        'tenancy': mdata['tenancy_ocid'],
        'region': mdata['region_name'],
        'key_content': mdata['private_key'],
        'fingerprint': mdata['fingerprint'],
    })

    vnic = vnet_client.get_vnic(mdata['vnic_ocid'])
    if vnic.status != 200:
        raise RequestError('Oracle vnic bad status %s' % vnic.status)

    if not vnic.data.skip_source_dest_check:
        vnic_opts = oci.core.models.UpdateVnicDetails(
            skip_source_dest_check=True,
        )
        vnet_client.update_vnic(mdata['vnic_ocid'], vnic_opts)
        time.sleep(0.25)

    private_ips = vnet_client.list_private_ips(vnic_id=mdata['vnic_ocid'])
    if private_ips.status != 200:
        raise RequestError('Oracle private ip bad status %s' % \
            private_ips.status)

    private_ip_ocid = None
    subnet_ocid = None
    for private_ip in private_ips.data:
        private_ip_ocid = private_ip.id
        subnet_ocid = private_ip.subnet_id
        break

    if not private_ip_ocid or not subnet_ocid:
        raise ValueError('Failed to find Oracle vnic ocid info')

    subnet = vnet_client.get_subnet(subnet_ocid)
    if subnet.status != 200:
        raise RequestError('Oracle subnet bad status %s' % subnet.status)

    vcn_ocid = subnet.data.vcn_id

    tables = vnet_client.list_route_tables(
        compartment_id=mdata['compartment_ocid'],
        vcn_id=vcn_ocid,
    )
    if tables.status != 200:
        raise RequestError('Oracle tables bad status %s' % tables.status)

    for table in tables.data:
        exists = False
        replace = False

        route_rules = []
        for route in table.route_rules:
            if route.cidr_block == dest_network:
                exists = True

                if route.network_entity_id != private_ip_ocid:
                    route.network_entity_id = private_ip_ocid
                    replace = True

            route_rules.append(route)

        if exists and not replace:
            continue

        if not replace:
            route_rules.append(oci.core.models.RouteRule(
                cidr_block=dest_network,
                network_entity_id=private_ip_ocid,
                destination_type='CIDR_BLOCK',
            ))

        table_opts = oci.core.models.UpdateRouteTableDetails(
            route_rules=route_rules,
        )

        vnet_client.update_route_table(table.id, table_opts)
