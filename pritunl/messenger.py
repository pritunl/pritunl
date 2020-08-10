from pritunl.helpers import *
from pritunl import mongo
from pritunl import cache
from pritunl import utils

import pymongo
import time

def publish(channels, message, extra=None, transaction=None):
    if cache.has_cache:
        return cache.publish(channels, message, extra=extra)

    collection = mongo.get_collection('messages')
    doc = {
        'message': message,
        'timestamp': utils.now(),
    }

    if extra:
        for key, val in list(extra.items()):
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
                'nonce': utils.ObjectId(),
            }, {
                '$set': doc,
            }, upsert=True)
        else:
            for channel in channels:
                doc_copy = doc.copy()
                doc_copy['channel'] = channel

                tran_collection.bulk().find({
                    'nonce': utils.ObjectId(),
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
    if cache.has_cache:
        if not isinstance(channels, str):
            raise TypeError(
                'Cannot get cache cursor_id for muiltiple channels')
        return cache.get_cursor_id(channels)

    collection = mongo.get_collection('messages')
    spec = {}

    if isinstance(channels, str):
        spec['channel'] = channels
    else:
        spec['channel'] = {'$in': channels}

    for i in range(2):
        try:
            return collection.find(spec).sort(
                '$natural', pymongo.DESCENDING)[0]['_id']
        except IndexError:
            if i:
                raise
            else:
                publish(channels, None)

@interrupter_generator
def subscribe(channels, cursor_id=None, timeout=None, yield_delay=None,
        yield_app_server=False):
    if cache.has_cache:
        for msg in cache.subscribe(channels, cursor_id=cursor_id,
                timeout=timeout, yield_delay=yield_delay,
                yield_app_server=yield_app_server):
            yield msg
        return

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

            cursor = collection.find(
                spec,
                cursor_type=pymongo.cursor.CursorType.TAILABLE_AWAIT,
            ).sort('$natural', pymongo.ASCENDING)

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

                if yield_app_server and check_app_server_interrupt():
                    return

                if timeout and time.time() - start_time >= timeout:
                    return

                yield

        except pymongo.errors.AutoReconnect:
            time.sleep(0.2)
