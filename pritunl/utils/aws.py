from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings

import boto3
import requests
import time

def connect_ec2(aws_key, aws_secret, region):
    return boto3.client(
        'ec2',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name=region,
    )

def connect_route53(aws_key, aws_secret, region):
    return boto.route53.connect_to_region(
        region,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
    )

def get_instance_id():
    try:
        resp = requests.get(
            'http://169.254.169.254/latest/meta-data/instance-id',
            timeout=0.5,
        )

        if resp.status_code != 200:
            return

        return resp.content
    except:
        pass

def add_vpc_route(region, vpc_id, network, resource_id):
    time.sleep(0.1)

    region_key = region.replace('-', '_')
    aws_key = getattr(settings.app, region_key + '_access_key')
    aws_secret = getattr(settings.app, region_key + '_secret_key')
    ipv6 = ':' in network

    if not aws_key or not aws_secret:
        raise ValueError('AWS credentials not available for %s' % region)

    if aws_key == 'role':
        aws_key = None
    if aws_secret == 'role':
        aws_secret = None

    vpc_conn = connect_ec2(aws_key, aws_secret, region)

    response = vpc_conn.describe_route_tables(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ],
            },
        ],
    )
    if not response:
        raise VpcRouteTableNotFound('Failed to find VPC routing table')

    instance_id = None
    interface_id = None
    if resource_id.startswith('eni-'):
        interface_id = resource_id
    else:
        instance_id = resource_id

    for table in response['RouteTables']:
        table_id = table.get('RouteTableId')
        if not table_id:
            continue

        exists = False
        replace = False
        for route in table['Routes']:
            if ipv6:
                if route.get('DestinationIpv6CidrBlock') != network:
                    continue
            else:
                if route.get('DestinationCidrBlock') != network:
                    continue
            exists = True

            if interface_id:
                if route.get('NetworkInterfaceId') != interface_id:
                    replace = True
            else:
                if route.get('InstanceId') != instance_id:
                    replace = True

            break

        if exists and not replace:
            continue

        params = {
            'RouteTableId': table_id,
        }

        if interface_id:
            params['NetworkInterfaceId'] = interface_id
        else:
            params['InstanceId'] = instance_id

        if ipv6:
            params['DestinationIpv6CidrBlock'] = network
        else:
            params['DestinationCidrBlock'] = network

        if replace:
            try:
                response = vpc_conn.create_route(**params)
                if not response['Return']:
                    raise ValueError('Invalid response')
            except:
                vpc_conn.replace_route(**params)
        else:
            try:
                vpc_conn.replace_route(**params)
            except:
                response = vpc_conn.create_route(**params)
                if not response['Return']:
                    raise ValueError('Invalid response')

def get_vpcs():
    vpcs_data = {}

    for region in AWS_REGIONS:
        region_key = region.replace('-', '_')
        aws_key = getattr(settings.app, region_key + '_access_key')
        aws_secret = getattr(settings.app, region_key + '_secret_key')
        vpc_data = []
        vpcs_data[region] = vpc_data

        if not aws_key or not aws_secret:
            continue

        if aws_key == 'role':
            aws_key = None
        if aws_secret == 'role':
            aws_secret = None

        vpc_conn = connect_vpc(aws_key, aws_secret, region)

        vpcs = vpc_conn.get_all_vpcs()
        for vpc in vpcs:
            vpc_data.append({
                'id': vpc.id,
                'network': vpc.cidr_block,
            })

    return vpcs_data

def get_zones():
    zones_data = {}

    for region in AWS_REGIONS:
        region_key = region.replace('-', '_')
        aws_key = getattr(settings.app, region_key + '_access_key')
        aws_secret = getattr(settings.app, region_key + '_secret_key')
        zone_data = []
        zones_data[region] = zone_data

        if not aws_key or not aws_secret:
            continue

        if aws_key == 'role':
            aws_key = None
        if aws_secret == 'role':
            aws_secret = None

        conn = connect_route53(aws_key, aws_secret, region)

        for zone in conn.get_zones():
            zone_data.append(zone.name)

    return zones_data

def set_zone_record(region, zone_name, host_name, ip_addr, ip_addr6):
    region_key = region.replace('-', '_')
    aws_key = getattr(settings.app, region_key + '_access_key')
    aws_secret = getattr(settings.app, region_key + '_secret_key')

    if aws_key == 'role':
        aws_key = None
    if aws_secret == 'role':
        aws_secret = None

    conn = connect_route53(aws_key, aws_secret, region)

    zone = conn.get_zone(zone_name)
    record_name = host_name + '.' + zone_name
    record_name_trim = record_name.rstrip('.')
    zone_host_name = None
    zone_host_name6 = None

    if ip_addr:
        zone_host_name = record_name_trim
        try:
            zone.add_record('A', record_name, ip_addr)
        except:
            zone.update_a(record_name, ip_addr)
    else:
        try:
            zone.delete_a(record_name)
        except:
            pass

    if ip_addr6:
        zone_host_name6 = record_name_trim
        try:
            zone.add_record('AAAA', record_name, ip_addr6)
        except:
            old_record = zone.find_records(record_name, 'AAAA', all=False)
            zone.update_record(old_record, ip_addr6)
    else:
        try:
            old_record = zone.find_records(record_name, 'AAAA', all=False)
            zone.delete_record(old_record)
        except:
            pass

    return zone_host_name, zone_host_name6
