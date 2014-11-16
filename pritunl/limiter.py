from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import wsgiserver

import time

_get_time = time.time
peers_expire_count = {}

class CherryPyWSGIServerLimited(wsgiserver.CherryPyWSGIServer):
	def validate_peer(self, peer):
		cur_time = _get_time()
		peer = peer[0]
		expire, count = peers_expire_count.get(peer, (None, None))
		if expire and cur_time <= expire:
			if count > settings.app.peer_limit:
				return False
			peers_expire_count[peer] = (expire, count + 1)
		else:
			peers_expire_count[peer] = (
				cur_time + settings.app.peer_limit_timeout, 1)
		return True

	def validate_request(self, peer, request):
		return self.validate_peer(peer)
