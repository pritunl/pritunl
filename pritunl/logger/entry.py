from pritunl.constants import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import utils

import pymongo

class LogEntry(mongo.MongoObject):
    fields = {
        'timestamp',
        'message',
    }

    def __init__(self, message=None, **kwargs):
        mongo.MongoObject.__init__(self)

        if message is not None:
            self.message = message

        if not self.exists:
            self.timestamp = utils.now()
            self.commit()

    def dict(self):
        return {
            'id': self.id,
            'timestamp': int(self.timestamp.strftime('%s')),
            'message': self.message,
        }

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('log_entries')

    def commit(self, *args, **kwargs):
        from pritunl import event
        mongo.MongoObject.commit(self, *args, **kwargs)
        event.Event(type=LOG_UPDATED)

def iter_log_entries():
    for doc in LogEntry.collection.find().sort(
            'timestamp', pymongo.DESCENDING):
        yield LogEntry(doc=doc)
