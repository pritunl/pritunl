from pritunl.mongo.dict import MongoDict
from pritunl.mongo.list import MongoList
from pritunl.mongo.object import MongoObject

database = None
secondary_database = None
prefix = ''
collection_types = {}

def get_collection(name):
    coll_type = collection_types.get(name)
    if coll_type == 1:
        coll = getattr(database, prefix + name)
    elif coll_type == 2:
        coll = getattr(secondary_database, prefix + name)
    else:
        raise TypeError('Invalid collection name')

    coll.name_str = name
    return coll
