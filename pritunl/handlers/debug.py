from pritunl.constants import *
from pritunl.exceptions import *
import pritunl.utils as utils
from pritunl.cache import cache_db
from pritunl import app_server
import collections

@app_server.app.route('/debug/db_dump', methods=['GET'])
@app_server.auth
def debug_db_dump():
    if not app_server.debug:
        return flask.abort(404)
    data = {}
    data_copy = cache_db._data.copy()
    for key in data_copy:
        value = data_copy[key]['val']
        if isinstance(value, (set, collections.deque)):
            value = list(value)
        data[key] = value
    return utils.jsonify(data)
