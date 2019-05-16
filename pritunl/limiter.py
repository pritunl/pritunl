from pritunl import settings
from pritunl import mongo
from pritunl import utils

import time
import datetime

_get_time = time.time
limiters = []

class Limiter(object):
    def __init__(self, group_name, limit_name, limit_timeout_name):
        limiters.append(self)
        self.peers_expire_count = {}
        self.group_name = group_name
        self.limit_name = limit_name
        self.limit_timeout_name = limit_timeout_name

    def validate(self, peer):
        settings_group = getattr(settings, self.group_name)
        limit = getattr(settings_group, self.limit_name)
        limit_timeout = getattr(settings_group, self.limit_timeout_name)

        cur_time = _get_time()
        expire, count = self.peers_expire_count.get(peer, (None, None))
        if expire and cur_time <= expire:
            if count > limit:
                return False
            self.peers_expire_count[peer] = (expire, count + 1)
        else:
            self.peers_expire_count[peer] = (cur_time + limit_timeout, 1)
        return True

def auth_check(user_id):
    collection = mongo.get_collection('auth_limiter')

    doc = collection.find_and_modify({
        '_id': user_id,
    }, {
        '$inc': {'count': 1},
        '$setOnInsert': {'timestamp': utils.now()},
    }, new=True, upsert=True)

    if utils.now() > doc['timestamp'] + datetime.timedelta(
            seconds=settings.app.auth_limiter_ttl):
        doc = {
            'count': 1,
            'timestamp': utils.now(),
        }
        collection.update({
            '_id': user_id,
        }, doc, upsert=True)

    return doc['count'] <= settings.app.auth_limiter_count_max
