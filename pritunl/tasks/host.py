from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import utils
from pritunl import task
from pritunl import event
from pritunl import monitoring

import datetime

class TaskHost(task.Task):
    type = 'host'

    @cached_static_property
    def hosts_collection(cls):
        return mongo.get_collection('hosts')

    @interrupter
    def task(self):
        if settings.app.demo_mode:
            return

        try:
            cursor = self.hosts_collection.find({}, {
                '_id': True,
                'status': True,
                'ping_timestamp': True,
                'server_count': True,
                'device_count': True,
            })

            yield

            now = utils.now()
            ttl = datetime.timedelta(seconds=settings.app.host_ping_ttl)
            ttl_timestamp = {'$lt': now - ttl}
            server_count = 0
            device_count = 0

            for doc in cursor:
                if doc.get('status') == ONLINE:
                    server_count += doc.get('server_count') or 0
                    device_count += doc.get('device_count') or 0

                if doc.get('ping_timestamp') and \
                        now - doc['ping_timestamp'] > ttl:
                    response = self.hosts_collection.update({
                        '_id': doc['_id'],
                        'ping_timestamp': ttl_timestamp,
                    }, {'$set': {
                        'status': OFFLINE,
                        'ping_timestamp': None,
                    }})

                    yield

                    if response['updatedExisting']:
                        event.Event(type=HOSTS_UPDATED)

            yield

            monitoring.insert_point('cluster', {}, {
                'server_count': server_count,
                'device_count': device_count,
            })
        except GeneratorExit:
            raise
        except:
            logger.exception('Error checking host status', 'runners')

task.add_task(TaskHost, seconds=range(0, 60, settings.app.host_ping))
