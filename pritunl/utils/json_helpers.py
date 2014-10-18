from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo

import datetime
import bson
import time
import flask
import json

def json_object_hook_handler(obj):
    object_data = obj.get('__OBJ__')
    if object_data:
        object_type, object_data = object_data
        if object_type == 'OID':
            return bson.ObjectId(object_data)
        elif object_type == 'DATE':
            return datetime.datetime.fromtimestamp(object_data)
    return obj

def json_default(obj):
    if isinstance(obj, (mongo.MongoDict, mongo.MongoList)):
        return obj.data
    elif isinstance(obj, bson.ObjectId):
        return {'__OBJ__': ['OID', str(obj)]}
    elif isinstance(obj, datetime.datetime):
        return {'__OBJ__': ['DATE', time.mktime(obj.timetuple()) + (obj.microsecond / 1000000.)]}
    raise TypeError(repr(obj) + ' is not JSON serializable')

def jsonify(data=None, status_code=None):
    if not isinstance(data, basestring):
        data = json.dumps(data)
    response = flask.Response(response=data, mimetype='application/json')
    response.headers.add('Cache-Control',
        'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', 0)
    if status_code is not None:
        response.status_code = status_code
    return response
