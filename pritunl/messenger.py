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
        'timestamp': datetime.datetime.utcnow(),
        'message': message,
    }

    if extra:
        for key, val in extra.items():
            doc[key] = val

    if transaction:
        tran_collection = transaction.collection(
            collection.name_str)

        if isinstance(channels, str):
            doc['channel'] = channels
            tran_collection.update({
                '_id': bson.ObjectId(),
            }, doc, upsert=True)
        else:
            for channel in channels:
                doc_copy = doc.copy()
                doc_copy['channel'] = channel

                tran_collection.bulk().find({
                    '_id': bson.ObjectId(),
                }).upsert().update(doc_copy)
            tran_collection.bulk_execute()
    else:
        if isinstance(channels, str):
            doc['channel'] = channels
            docs = doc
        else:
            docs = []
            for channel in channels:
                doc_copy = doc.copy()
                doc_copy['channel'] = channel
                docs.append(doc_copy)
        collection.insert(docs)

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
        pass

def subscribe(channels, cursor_id=None, timeout=None,
        yield_delay=None):
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
                    yield doc

                    if yield_delay:
                        time.sleep(yield_delay)

                        spec = {
                            '_id': {'$gt': cursor_id},
                            'channel': channels,
                        }
                        cursor = collection.find(spec).sort(
                            '$natural', pymongo.ASCENDING)

                        for doc in cursor:
                            yield doc

                        return
                if timeout and time.time() - start_time >= timeout:
                    return
        except pymongo.errors.AutoReconnect:
            time.sleep(0.2)
