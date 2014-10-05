from pritunl.mongo.dict import MongoDict
from pritunl.mongo.list import MongoList
from pritunl.mongo.object import MongoObject

import pymongo

has_bulk = all((
    hasattr(pymongo.collection.Collection, 'initialize_ordered_bulk_op'),
    hasattr(pymongo.collection.Collection, 'initialize_unordered_bulk_op'),
))
collections = {}

def get_collection(name):
    return collections[name]

__all__ = (
    'MongoDict',
    'MongoList',
    'MongoObject',
    'has_bulk',
    'collections',
    'get_collection',
)
