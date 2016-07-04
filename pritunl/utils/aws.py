from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import settings

import boto
import boto.ec2
import boto.vpc
import requests

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
    region_key = region.replace('-', '_')
    aws_key = getattr(settings.app, region_key + '_access_key')
    aws_secret = getattr(settings.app, region_key + '_secret_key')

    if not aws_key or not aws_secret:
        raise ValueError('AWS credentials not available for %s' % region)

    vpc_conn = boto.connect_vpc(
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region=boto.ec2.get_region(region),
    )

    tables = vpc_conn.get_all_route_tables(filters={'vpc-id': vpc_id})
    if not tables:
        raise VpcRouteTableNotFound('Failed to find VPC routing table')

    instance_id = None
    interface_id = None
    if resource_id.startswith('eni-'):
        interface_id = resource_id
    else:
        instance_id = resource_id

    for table in tables:
        try:
            vpc_conn.create_route(
                table.id,
                network,
                instance_id=instance_id,
                interface_id=interface_id,
            )
        except:
            vpc_conn.replace_route(
                table.id,
                network,
                instance_id=instance_id,
                interface_id=interface_id,
            )

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

        vpc_conn = boto.connect_vpc(
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region=boto.ec2.get_region(region),
        )

        vpcs = vpc_conn.get_all_vpcs()
        for vpc in vpcs:
            vpc_data.append({
                'id': vpc.id,
                'network': vpc.cidr_block,
            })

    return vpcs_data

def get_zones():
    zones = []

    for region in AWS_REGIONS:
        region_key = region.replace('-', '_')
        aws_key = getattr(settings.app, region_key + '_access_key')
        aws_secret = getattr(settings.app, region_key + '_secret_key')

        if not aws_key or not aws_secret:
            continue

        conn = boto.route53.connect_to_region(
            region,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
        )

        for zone in conn.get_zones():
            zones.append(zone.name)

    return zones
