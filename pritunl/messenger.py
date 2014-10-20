from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import utils

import pymongo
import time
import datetime
import bson

def publish(channels, message, extra=None, transaction=None):
    collection = mongo.get_collection('messages')
    doc = {
        'message': message,
        'timestamp': utils.now(),
    }

    if extra:
        for key, val in extra.items():
            doc[key] = val

    # ObjectId must be set by server and ObjectId order must match $natural
    # order. Docs sent in order on client are not guaranteed to match $natural
    # order on server. Nonce is added to force an insert from upsert where
    # insert is not supported.
    # When using inserts manipulate=False must be set to prevent pymongo
    # from setting ObjectId locally.
    if transaction:
        tran_collection = transaction.collection(collection.name_str)

        if isinstance(channels, str):
            doc['channel'] = channels
            tran_collection.update({
                'nonce': bson.ObjectId(),
            }, {
                '$set': doc,
            }, upsert=True)
        else:
            for channel in channels:
                doc_copy = doc.copy()
                doc_copy['channel'] = channel

                tran_collection.bulk().find({
                    'nonce': bson.ObjectId(),
                }).upsert().update({
                    '$set': doc_copy,
                })
            tran_collection.bulk_execute()
    else:
        if isinstance(channels, str):
            doc['channel'] = channels
            collection.insert(doc, manipulate=False)
        else:
            docs = []
            for channel in channels:
                doc_copy = doc.copy()
                doc_copy['channel'] = channel
                docs.append(doc_copy)
            collection.insert(docs, manipulate=False)

def get_cursor_id(channels):
    collection = mongo.get_collection('messages')
    spec = {}

    if isinstance(channels, str):
        spec['channel'] = channels
    else:
        spec['channel'] = {'$in': channels}

    for i in xrange(2):
        try:
            return collection.find(spec).sort(
                '$natural', pymongo.DESCENDING)[0]['_id']
        except IndexError:
            if i:
                raise
            else:
                publish(channels, None)

@interrupter_generator
def subscribe(channels, cursor_id=None, timeout=None, yield_delay=None):
    collection = mongo.get_collection('messages')
    start_time = time.time()
    cursor_id = cursor_id or get_cursor_id(channels)
    while True:
        try:
            spec = {}

            if isinstance(channels, str):
                spec['channel'] = channels
            else:
                spec['channel'] = {'$in': channels}

            if cursor_id:
                spec['_id'] = {'$gt': cursor_id}

            yield

            cursor = collection.find(spec, tailable=True,
                await_data=True).sort('$natural', pymongo.ASCENDING)

            yield

            while cursor.alive:
                for doc in cursor:
                    cursor_id = doc['_id']

                    yield

                    if doc.get('message') is not None:
                        doc.pop('nonce', None)
                        yield doc

                    if yield_delay:
                        time.sleep(yield_delay)

                        spec = spec.copy()
                        spec['_id'] = {'$gt': cursor_id}
                        cursor = collection.find(spec).sort(
                            '$natural', pymongo.ASCENDING)

                        for doc in cursor:
                            if doc.get('message') is not None:
                                doc.pop('nonce', None)
                                yield doc

                        return

                if timeout and time.time() - start_time >= timeout:
                    return

                yield

        except pymongo.errors.AutoReconnect:
            time.sleep(0.2)
