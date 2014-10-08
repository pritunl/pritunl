from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import mongo

import pymongo
import time
import datetime
import bson

def publish(channels, message, extra=None, transaction=None):
    collection = mongo.get_collection('messages')
    doc = {
        'message': message,
    }

    if extra:
        for key, val in extra.items():
            doc[key] = val

    if transaction:
        collection = transaction.collection(collection.name_str)

    # ObjectId and timestamp must be set by server and ObjectId order must
    # match $natural order. Docs sent in order on client are not guaranteed
    # to match $natural order on server. Nonce is added to force an insert
    # from upsert to allow the use of $currentDate.
    # When using inserts manipulate=False must be set to prevent pymongo
    # from setting ObjectId locally.
    if isinstance(channels, str):
        doc['channel'] = channels

        collection.update({
            'nonce': bson.ObjectId(),
        }, {
            '$set': doc,
            '$currentDate': {
                'timestamp': True,
            },
        }, upsert=True)
    else:
        if transaction:
            for channel in channels:
                doc_copy = doc.copy()
                doc_copy['channel'] = channel

                tran_collection.bulk().find({
                    'nonce': bson.ObjectId(),
                }).upsert().update({
                    '$set': doc_copy,
                    '$currentDate': {
                        'timestamp': True,
                    },
                })
            tran_collection.bulk_execute()
        else:
            bulk = collection.initialize_ordered_bulk_op()
            for channel in channels:
                doc_copy = doc.copy()
                doc_copy['channel'] = channel

                bulk.find({
                    'nonce': bson.ObjectId(),
                }).upsert().update({
                    '$set': doc_copy,
                    '$currentDate': {
                        'timestamp': True,
                    },
                })
            bulk.execute()

def get_cursor_id(channels):
    collection = mongo.get_collection('messages')
    spec = {}

    if isinstance(channels, str):
        spec['channel'] = channels
    else:
        spec['channel'] = {'$in': channels}

    try:
        return collection.find(spec).sort(
            '$natural', pymongo.DESCENDING)[0]['_id']
    except IndexError:
        publish(channels, None)
        return collection.find(spec).sort(
            '$natural', pymongo.DESCENDING)[0]['_id']

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

            cursor = collection.find(spec, tailable=True,
                await_data=True).sort('$natural', pymongo.ASCENDING)

            while cursor.alive:
                for doc in cursor:
                    cursor_id = doc['_id']
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
        except pymongo.errors.AutoReconnect:
            time.sleep(0.2)
