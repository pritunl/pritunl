import pymongo

has_bulk = all((
    hasattr(pymongo.collection.Collection, 'initialize_ordered_bulk_op'),
    hasattr(pymongo.collection.Collection, 'initialize_unordered_bulk_op'),
))
collections = {}

def get_collection(name):
    return collections[name]
