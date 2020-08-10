from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings

import boto.utils
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

def get_metadata():
    metadata = boto.utils.get_instance_metadata()

    instance_id = metadata['instance-id']
    availability_zone = metadata['placement']['availability-zone']
    vpc_id = None
    region = None

    for aws_region in AWS_REGIONS:
        if availability_zone.startswith(aws_region):
            region = aws_region
            break

    for iface in list(metadata['network']['interfaces']['macs'].values()):
        vpc_id = iface['vpc-id']
        break

    if not vpc_id:
        raise ValueError('Failed to get AWS VPC ID')

    if not region:
        raise ValueError('Failed to get AWS region')

    return {
        'instance_id': instance_id,
        'availability_zone': availability_zone,
        'vpc_id': vpc_id,
        'region': region,
    }

def add_vpc_route(network):
    time.sleep(0.1)

    mdata = get_metadata()
    region_key = mdata['region'].replace('-', '_')
    aws_key = getattr(settings.app, region_key + '_access_key')
    aws_secret = getattr(settings.app, region_key + '_secret_key')
    ipv6 = ':' in network

    if not aws_key or not aws_secret:
        raise ValueError('AWS credentials not available for %s' % region)

    if aws_key == 'role':
        aws_key = None
    if aws_secret == 'role':
        aws_secret = None

    ec2_conn = connect_ec2(aws_key, aws_secret, mdata['region'])

    response = ec2_conn.describe_route_tables(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    mdata['vpc_id'],
                ],
            },
        ],
    )
    if not response:
        raise VpcRouteTableNotFound('Failed to find VPC routing table')

    instance_id = mdata['instance_id']
    interface_id = None

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
                response = ec2_conn.create_route(**params)
                if not response['Return']:
                    raise ValueError('Invalid response')
            except:
                ec2_conn.replace_route(**params)
        else:
            try:
                ec2_conn.replace_route(**params)
            except:
                response = ec2_conn.create_route(**params)
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

        ec2_conn = connect_ec2(aws_key, aws_secret, region)

        response = ec2_conn.describe_vpcs()
        for vpc in response['Vpcs']:
            vpc_data.append({
                'id': vpc['VpcId'],
                'network': vpc['CidrBlock'],
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

        client = boto3.client(
            'route53',
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
        )

        hosted_zone_id = None
        hosted_zone_name = None
        hosted_zones = client.list_hosted_zones_by_name()
        for hosted_zone in hosted_zones['HostedZones']:
            zone_data.append(hosted_zone['Name'])

    return zones_data

def set_zone_record(region, zone_name, host_name, ip_addr, ip_addr6):
    region_key = region.replace('-', '_')
    aws_key = getattr(settings.app, region_key + '_access_key')
    aws_secret = getattr(settings.app, region_key + '_secret_key')

    if aws_key == 'role':
        aws_key = None
    if aws_secret == 'role':
        aws_secret = None

    client = boto3.client(
        'route53',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
    )

    hosted_zone_id = None
    hosted_zone_name = None
    hosted_zones = client.list_hosted_zones_by_name()
    for hosted_zone in hosted_zones['HostedZones']:
        if hosted_zone['Name'].startswith(zone_name):
            hosted_zone_id = hosted_zone['Id']
            hosted_zone_name = hosted_zone['Name']

    if not hosted_zone_id or not hosted_zone_name:
        raise ValueError('Route53 zone not found')

    record_name = host_name + '.' + hosted_zone_name

    records = client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id,
    )

    cur_ip_addr = None
    cur_ip_addr6 = None

    for record in records['ResourceRecordSets']:
        if record.get('Type') not in ('A', 'AAAA'):
            continue
        if record.get('Name') != record_name:
            continue

        if len(record['ResourceRecords']) == 1:
            if record['Type'] == 'A':
                cur_ip_addr = record['ResourceRecords'][0]['Value']
            else:
                cur_ip_addr6 = record['ResourceRecords'][0]['Value']
        else:
            if record['Type'] == 'A':
                cur_ip_addr = []
            else:
                cur_ip_addr6 = []

            for val in record['ResourceRecords']:
                if record['Type'] == 'A':
                    cur_ip_addr.append(val['Value'])
                else:
                    cur_ip_addr6.append(val['Value'])

    changes = []

    if ip_addr != cur_ip_addr:
        if not ip_addr and cur_ip_addr:
            if isinstance(cur_ip_addr, list):
                vals = cur_ip_addr
            else:
                vals = [cur_ip_addr]

            resource_recs = []
            for val in vals:
                resource_recs.append({'Value': val})

            changes.append({
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': record_name,
                    'Type': 'A',
                    'TTL': 60,
                    'ResourceRecords': resource_recs,
                },
            })
        else:
            changes.append({
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': record_name,
                    'Type': 'A',
                    'TTL': 60,
                    'ResourceRecords': [
                        {'Value': ip_addr},
                    ],
                },
            })

    if ip_addr6 != cur_ip_addr6:
        if not ip_addr6 and cur_ip_addr6:
            if isinstance(cur_ip_addr6, list):
                vals = cur_ip_addr6
            else:
                vals = [cur_ip_addr6]

            resource_recs = []
            for val in vals:
                resource_recs.append({'Value': val})

            changes.append({
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': record_name,
                    'Type': 'AAAA',
                    'TTL': 60,
                    'ResourceRecords': resource_recs,
                },
            })
        else:
            changes.append({
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': record_name,
                    'Type': 'AAAA',
                    'TTL': 60,
                    'ResourceRecords': [
                        {'Value': ip_addr6},
                    ],
                },
            })

    if changes:
        client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': changes,
            },
        )

    zone_host_name = None
    zone_host_name6 = None
    if ip_addr:
        zone_host_name = record_name.rstrip('.')
    if ip_addr6:
        zone_host_name6 = record_name.rstrip('.')

    return zone_host_name, zone_host_name6
