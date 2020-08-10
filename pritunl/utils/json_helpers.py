from pritunl.utils.misc import ObjectId, fnv32a

from pritunl.constants import *
from pritunl import mongo

import datetime
import calendar
import flask
import json
import bson
import bson.tz_util
import bson.objectid

_demo_cache = {}

def json_object_hook_handler(obj):
    obj_data = obj.get('$obj')
    if obj_data:
        object_type, obj_data = obj_data
        if object_type == 'oid':
            return ObjectId(obj_data)
        elif object_type == 'date':
            return datetime.datetime.fromtimestamp(obj_data / 1000.,
                bson.tz_util.utc)
    return obj

def json_default(obj):
    if isinstance(obj, (mongo.MongoDict, mongo.MongoList)):
        return obj.data
    elif isinstance(obj, bson.objectid.ObjectId):
        return {'$obj': ['oid', str(obj)]}
    elif isinstance(obj, datetime.datetime):
        return {'$obj': ['date', int(calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000)]}

    raise TypeError(repr(obj) + ' is not JSON serializable')

def jsonify(data=None, status_code=None):
    if not isinstance(data, str):
        data = json.dumps(data, default=lambda x: str(x))
    response = flask.Response(response=data, mimetype='application/json')
    response.headers.add('Cache-Control',
        'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', 0)
    if status_code is not None:
        response.status_code = status_code
    return response

def demo_blocked():
    return jsonify({
        'error': DEMO_BLOCKED,
        'error_msg': DEMO_BLOCKED_MSG,
    }, 400)

def demo_cache_id(*args):
    return fnv32a(flask.request.path + ':' + '.'.join([str(x) for x in args]))

def demo_set_cache(data, *args):
    cache_id = demo_cache_id(*args)
    _demo_cache[cache_id] = data

def demo_get_cache(*args):
    cache_id = demo_cache_id(*args)
    return _demo_cache.get(cache_id)
