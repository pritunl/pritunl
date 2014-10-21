from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

import pymongo
import random
import flask
import time
import bson

# For MongoDict MongoList
# class JSONEncoderPatched(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, (MongoDict, MongoList)):
#             return obj.data
#         raise TypeError(repr(obj) + ' is not JSON serializable')
# dumps_orig = json.dumps
# def dumps_patched(*args, **kwargs):
#     if not kwargs.get('cls'):
#         kwargs['cls'] = JSONEncoderPatched
#     return dumps_orig(*args, **kwargs)
# json.dumps = dumps_patched

_mongo_errors = []
for error_attr in (
            'AutoReconnect',
            'ConnectionFailure',
            'ExecutionTimeout',
            'WTimeoutError',
        ):
    if hasattr(pymongo.errors, error_attr):
        _mongo_errors.append(getattr(pymongo.errors, error_attr))

insert_orig = pymongo.collection.Collection.insert
def insert(self, *args, **kwargs):
    if flask.ctx.has_request_context():
        flask.g.write_count += 1
        start = time.time()
    else:
        start = None
    if RANDOM_ERROR_RATE and random.random() <= RANDOM_ERROR_RATE:
        raise random.choice(_mongo_errors)('Test error')
    val = insert_orig(self, *args, **kwargs)
    if start:
        flask.g.query_time += (time.time() - start)
    return val

pymongo.collection.Collection.insert = insert

update_orig = pymongo.collection.Collection.update
def update(self, *args, **kwargs):
    if flask.ctx.has_request_context():
        flask.g.write_count += 1
        start = time.time()
    else:
        start = None
    if RANDOM_ERROR_RATE and random.random() <= RANDOM_ERROR_RATE:
        raise random.choice(_mongo_errors)('Test error')
    val = update_orig(self, *args, **kwargs)
    if start:
        flask.g.query_time += (time.time() - start)
    return val
pymongo.collection.Collection.update = update

remove_orig = pymongo.collection.Collection.remove
def remove(self, *args, **kwargs):
    if flask.ctx.has_request_context():
        flask.g.write_count += 1
        start = time.time()
    else:
        start = None
    if RANDOM_ERROR_RATE and random.random() <= RANDOM_ERROR_RATE:
        raise random.choice(_mongo_errors)('Test error')
    val = remove_orig(self, *args, **kwargs)
    if start:
        flask.g.query_time += (time.time() - start)
    return val
pymongo.collection.Collection.remove = remove

find_orig = pymongo.collection.Collection.find
def find(self, *args, **kwargs):
    if flask.ctx.has_request_context() and \
            not (args and \
            isinstance(args[0], bson.SON) and \
            'count' in args[0]):
        flask.g.query_count += 1
        start = time.time()
    else:
        start = None
    if RANDOM_ERROR_RATE and random.random() <= RANDOM_ERROR_RATE:
        raise random.choice(_mongo_errors)('Test error')
    val = find_orig(self, *args, **kwargs)
    if start:
        flask.g.query_time += (time.time() - start)
    return val
pymongo.collection.Collection.find = find

find_and_modify_orig = pymongo.collection.Collection.find_and_modify
def find_and_modify(self, *args, **kwargs):
    if flask.ctx.has_request_context():
        flask.g.write_count += 1
        start = time.time()
    else:
        start = None
    if RANDOM_ERROR_RATE and random.random() <= RANDOM_ERROR_RATE:
        raise random.choice(_mongo_errors)('Test error')
    val = find_and_modify_orig(self, *args, **kwargs)
    if start:
        flask.g.query_time += (time.time() - start)
    return val
pymongo.collection.Collection.find_and_modify = find_and_modify

aggregate_orig = pymongo.collection.Collection.aggregate
def aggregate(self, *args, **kwargs):
    if flask.ctx.has_request_context():
        flask.g.query_count += 1
        start = time.time()
    else:
        start = None
    if RANDOM_ERROR_RATE and random.random() <= RANDOM_ERROR_RATE:
        raise random.choice(_mongo_errors)('Test error')
    val = aggregate_orig(self, *args, **kwargs)
    if start:
        flask.g.query_time += (time.time() - start)
    return val
pymongo.collection.Collection.aggregate = aggregate

class ObjectId(bson.ObjectId):
    def __new__(cls, oid=None):
        # Patch for pritunl 0.10.x
        if oid and len(oid) != 24:
            return oid
        return object.__new__(cls)
bson.ObjectId = ObjectId
