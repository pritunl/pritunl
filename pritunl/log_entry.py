from constants import *
from descriptors import *
from event import Event
from mongo_object import MongoObject
import mongo
import time
import uuid
import pymongo

class LogEntry(MongoObject):
    fields = {
        'timestamp',
        'message',
    }

    def __init__(self, message=None, **kwargs):
        MongoObject.__init__(self, **kwargs)

        if message is not None:
            self.message = message

        if not self.exists:
            self.timestamp = datetime.datetime.now()
            self.commit()

    def dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%s'),
            'message': self.message,
        }

    @static_property
    def collection(cls):
        return mongo.get_collection('log_entries')

    def commit(self, *args, **kwargs):
        MongoObject.commit(self, *args, **kwargs)
        Event(type=LOG_UPDATED)

    @classmethod
    def iter_log_entries(cls):
        for doc in cls.collection.find().sort(
                'timestamp', pymongo.DESCENDING):
            yield cls(doc=doc)
