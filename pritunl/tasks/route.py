from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import messenger
from pritunl import utils
from pritunl import task

import datetime

class TaskRoute(task.Task):
    type = 'route'

    @cached_static_property
    def routes_collection(cls):
        return mongo.get_collection('routes_reserve')

    @interrupter
    def task(self):
        try:
            timestamp_spec = utils.now() - datetime.timedelta(
                seconds=settings.vpn.route_ping_ttl)

            docs = self.server_collection.find({
                'timestamp': {'$lt': timestamp_spec},
            })

            yield

            for doc in docs:
                server_id = doc['server_id']
                vpc_region = doc['vpc_region']
                vpc_id = doc['vpc_id']
                network = doc['network']

                messenger.publish('instance', ['route_advertisement',
                    server_id, vpc_region, vpc_id, network])
        except GeneratorExit:
            raise
        except:
            logger.exception('Error checking route states', 'tasks')

        yield interrupter_sleep(settings.vpn.server_ping)

task.add_task(TaskRoute, seconds=xrange(0, 60, settings.vpn.server_ping))
