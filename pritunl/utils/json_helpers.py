from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo

import datetime
import time
import calendar
import flask
import json
import bson
import bson.tz_util

def json_object_hook_handler(obj):
    obj_data = obj.get('$obj')
    if obj_data:
        object_type, obj_data = obj_data
        if object_type == 'oid':
            return bson.ObjectId(obj_data)
        elif object_type == 'date':
            return datetime.datetime.fromtimestamp(obj_data / 1000.,
                bson.tz_util.utc)
    return obj

def json_default(obj):
    if isinstance(obj, (mongo.MongoDict, mongo.MongoList)):
        return obj.data
    elif isinstance(obj, bson.ObjectId):
        return {'$obj': ['oid', str(obj)]}
    elif isinstance(obj, datetime.datetime):
        return {'$obj': ['date', int(calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000)]}
    raise TypeError(repr(obj) + ' is not JSON serializable')

def jsonify(data=None, status_code=None):
    if not isinstance(data, basestring):
        data = json.dumps(data, default=lambda x: str(x))
    response = flask.Response(response=data, mimetype='application/json')
    response.headers.add('Cache-Control',
        'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', 0)
    if status_code is not None:
        response.status_code = status_code
    return response
