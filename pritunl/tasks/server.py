from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import messenger
from pritunl import utils
from pritunl import task
from pritunl import host

import datetime
import collections

class TaskServer(task.Task):
    type = 'server'

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def host_collection(cls):
        return mongo.get_collection('hosts')

    @interrupter
    def task(self):
        if settings.app.demo_mode:
            return

        try:
            timestamp = utils.now()
            timestamp_spec = timestamp - datetime.timedelta(
                seconds=settings.vpn.server_ping_ttl)

            docs = self.server_collection.find({
                'instances.ping_timestamp': {'$lt': timestamp_spec},
            }, {
                '_id': True,
                'instances': True,
            })

            yield

            for doc in docs:
                for instance in doc['instances']:
                    if instance['ping_timestamp'] < timestamp_spec:
                        logger.warning('Removing instance doc', 'server',
                            server_id=doc['_id'],
                            instance_id=instance['instance_id'],
                            cur_timestamp=timestamp,
                            ttl_timestamp=timestamp_spec,
                            ping_timestamp=instance['ping_timestamp'],
                        )

                        self.server_collection.update({
                            '_id': doc['_id'],
                            'instances.instance_id': instance['instance_id'],
                        }, {
                            '$pull': {
                                'instances': {
                                    'instance_id': instance['instance_id'],
                                },
                            },
                            '$inc': {
                                'instances_count': -1,
                            },
                        })

            yield

            docs = self.host_collection.find({
                'status': ONLINE,
            }, {
                '_id': True,
                'availability_group': True,
            })

            yield

            hosts_group = {}
            for doc in docs:
                hosts_group[doc['_id']] = doc.get(
                    'availability_group', DEFAULT)

            yield

            response = self.server_collection.aggregate([
                {'$match': {
                    'status': ONLINE,
                    'start_timestamp': {'$lt': timestamp_spec},
                }},
                {'$project': {
                    '_id': True,
                    'hosts': True,
                    'instances': True,
                    'replica_count': True,
                    'availability_group': True,
                    'offline_instances_count': {
                        '$subtract': [
                            '$replica_count',
                            '$instances_count',
                        ],
                    }
                }},
                {'$match': {
                    'offline_instances_count': {'$gt': 0},
                }},
            ])

            yield

            recover_count = 0

            for doc in response:
                cur_avail_group = doc.get('availability_group', DEFAULT)

                hosts_set = set(doc['hosts'])
                group_best = None
                group_len_max = 0
                server_groups = collections.defaultdict(set)

                for hst in hosts_set:
                    avail_zone = hosts_group.get(hst)
                    if not avail_zone:
                        continue

                    server_groups[avail_zone].add(hst)
                    group_len = len(server_groups[avail_zone])

                    if group_len > group_len_max:
                        group_len_max = group_len
                        group_best = avail_zone
                    elif group_len == group_len_max and \
                            avail_zone == cur_avail_group:
                        group_best = avail_zone

                if group_best and cur_avail_group != group_best:
                    logger.info(
                        'Rebalancing server availability group',
                        'server',
                        server_id=doc['_id'],
                        current_availability_group=cur_avail_group,
                        new_availability_group=group_best,
                    )

                    self.server_collection.update({
                        '_id': doc['_id'],
                        'status': ONLINE,
                    }, {'$set': {
                        'instances': [],
                        'instances_count': 0,
                        'availability_group': group_best,
                    }})

                    messenger.publish('servers', 'rebalance', extra={
                        'server_id': doc['_id'],
                        'availability_group': group_best,
                    })

                    prefered_hosts = server_groups[group_best]
                else:
                    prefered_hosts = server_groups[cur_avail_group]

                active_hosts = set(
                    [x['host_id'] for x in doc['instances']])
                prefered_hosts = list(prefered_hosts - active_hosts)
                if not prefered_hosts:
                    continue

                if recover_count >= 3:
                    continue
                recover_count += 1

                logger.info('Recovering server state', 'server',
                    server_id=doc['_id'],
                    prefered_hosts=prefered_hosts,
                )

                messenger.publish('servers', 'start', extra={
                    'server_id': doc['_id'],
                    'send_events': True,
                    'prefered_hosts': host.get_prefered_hosts(
                        prefered_hosts, doc['replica_count'])
                })
        except GeneratorExit:
            raise
        except:
            logger.exception('Error checking server states', 'tasks')

task.add_task(TaskServer, seconds=range(0, 60, settings.vpn.server_ping))
