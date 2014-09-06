from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import pritunl.mongo as mongo
import pymongo
import time
import datetime
import bson

class Messenger(object):
    def __init__(self, channel):
        self.channel = channel

    @static_property
    def collection(cls):
        return mongo.get_collection('messages')

    def publish(self, message, transaction=None):
        if transaction:
            collection = transaction.collection(
                self.collection.collection_name)
        else:
            collection = self.collection

        collection.update({
            '_id': bson.ObjectId(),
        }, {
            'timestamp': datetime.datetime.utcnow(),
            'channel': self.channel,
            'message': message,
        }, upsert=True)

    def subscribe(self, cursor_id=None, timeout=None, yield_delay=None):
        start_time = time.time()
        if cursor_id is None:
            try:
                cursor_id = self.collection.find({
                    'channel': self.channel,
                }).sort('$natural', pymongo.DESCENDING)[0]['_id']
            except IndexError:
                cursor_id = None
        while True:
            try:
                spec = {
                    'channel': self.channel,
                }
                if cursor_id:
                    spec['_id'] = {'$gt': cursor_id}
                cursor = self.collection.find(spec, tailable=True,
                    await_data=True).sort('$natural', pymongo.ASCENDING)
                while cursor.alive:
                    for doc in cursor:
                        cursor_id = doc['_id']
                        yield doc

                        if yield_delay:
                            time.sleep(yield_delay)

                            spec = {
                                '_id': {'$gt': cursor_id},
                                'channel': self.channel,
                            }
                            cursor = self.collection.find(spec).sort(
                                '$natural', pymongo.ASCENDING)

                            for doc in cursor:
                                yield doc

                            return
                    if timeout and time.time() - start_time >= timeout:
                        return
            except pymongo.errors.AutoReconnect:
                time.sleep(0.2)
