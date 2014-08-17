from constants import *
from exceptions import *
from pritunl import app_server
import pymongo

client = pymongo.MongoClient(app_server.mongodb_url)
database = client.get_default_database()

collections = {
    'users': database.users,
    'organizations': database.organizations,
    'servers': database.servers,
}
collections['users'].ensure_index([
    ('org_id', pymongo.ASCENDING),
    ('type', pymongo.ASCENDING),
])
collections['users'].ensure_index([
    ('org_id', pymongo.ASCENDING),
    ('name', pymongo.ASCENDING),
])
collections['organizations'].ensure_index('type')
collections['server'].ensure_index('name')

def get_collection(name):
    return collections[name]
