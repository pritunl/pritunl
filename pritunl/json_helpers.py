from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.mongo.dict import MongoDict
from pritunl.mongo.list import MongoList
import datetime
import bson
import time

def object_hook_handler(obj):
    object_data = obj.get('__OBJ__')
    if object_data:
        object_type, object_data = object_data
        if object_type == 'OID':
            return bson.ObjectId(object_data)
        elif object_type == 'DATE':
            return datetime.datetime.fromtimestamp(object_data)
    return obj

def json_default(obj):
    if isinstance(obj, (MongoDict, MongoList)):
        return obj.data
    elif isinstance(obj, bson.ObjectId):
        return {'__OBJ__': ['OID', str(obj)]}
    elif isinstance(obj, datetime.datetime):
        return {'__OBJ__': ['DATE', time.mktime(obj.timetuple()) + (obj.microsecond / 1000000.)]}
    raise TypeError(repr(obj) + ' is not JSON serializable')
