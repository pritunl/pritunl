from pritunl import settings

import time

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
