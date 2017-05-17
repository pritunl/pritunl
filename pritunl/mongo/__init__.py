from pritunl.mongo.dict import MongoDict
from pritunl.mongo.list import MongoList
from pritunl.mongo.object import MongoObject

collections = {}

def get_collection(name):
    return collections[name]
