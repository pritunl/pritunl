from pritunl.mongo.dict import MongoDict
from pritunl.mongo.list import MongoList
from pritunl.mongo.object import MongoObject

database = None
secondary_database = None
collections = {}

def get_collection(name):
    return collections[name]
