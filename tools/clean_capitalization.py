import re
import json
import datetime
import pymongo

CONF_FILE_PATH = '/etc/pritunl.conf'

with open(CONF_FILE_PATH, 'r') as conf_file:
    mongodb_uri = json.loads(conf_file.read())['mongodb_uri']

print 'DATABASE CONNECT'

mongo_client = pymongo.MongoClient(mongodb_uri)
mongo_db = mongo_client.get_default_database()

response = mongo_db.users.aggregate([
    {'$match': {
        'type': 'client',
        'auth_type': {
            '$ne': 'local',
        },
    }},
    {'$addFields': {
        'lower_name': {'$toLower': '$name'},
    }},
    {'$group': {
        '_id': {
            'lower_name': '$lower_name',
            'auth_type': '$auth_type',
        },
        'docs': {'$push': {
            '_id': '$_id',
            'name': '$name',
            'auth_type': '$auth_type',
            'certificate': '$certificate',
        }},
        'count': {'$sum': 1},
    }},
    {'$match': {
        'count': {'$gt': 1},
    }},
])

operations = []

for doc in response:
    if len(doc['docs']) != 2:
        print 'ERROR Unexpected length'
        print doc
        exit(1)

    id0 = doc['docs'][0]['_id']
    name0 = doc['docs'][0]['name']
    date0 = datetime.datetime.strptime(
        re.findall(r'Not Before: ([^\n]+)', doc['docs'][0]['certificate'])[0],
        "%b %d %H:%M:%S %Y %Z",
    )
    id1 = doc['docs'][1]['_id']
    name1 = doc['docs'][1]['name']
    date1 = datetime.datetime.strptime(
        re.findall(r'Not Before: ([^\n]+)', doc['docs'][1]['certificate'])[0],
        "%b %d %H:%M:%S %Y %Z",
    )

    if name0.islower():
        new_name = name1
    else:
        new_name = name0

    if date0 > date1:
        operations.append({
            'remove': id1,
            'rename': id0,
            'new_name': new_name,
        })
        print 'REMOVE: %r %s [%s]' % (id1, date1, name1)
        print 'RENAME: %r %s [%s] -> [%s]' % (id0, date0, name0, new_name)
    else:
        operations.append({
            'remove': id0,
            'rename': id1,
            'new_name': new_name,
        })
        print 'REMOVE: %r %s [%s]' % (id0, date0, name0)
        print 'RENAME: %r %s [%s] -> [%s]' % (id1, date1, name1, new_name)

if len(operations) == 0:
    print 'ALL USERS CONSISTENT'
    print 'EXIT'
    exit()

confirm = str(raw_input('CONTINUE (y/n): ')).lower().strip()
if confirm != 'y':
    print 'EXIT'
    exit()

for operation in operations:
    remove_id = operation['remove']
    rename_id = operation['rename']
    new_name = operation['new_name']

    print 'REMOVING: %r' % remove_id

    mongo_db.users_audit.delete_many({'user_id': remove_id})
    mongo_db.users_net_link.delete_many({'user_id': remove_id})
    mongo_db.servers_ip_pool.update({
        'user_id': remove_id,
    }, {'$unset': {
        'org_id': '',
        'user_id': '',
    }})
    mongo_db.users.delete_one({'_id': remove_id})

    print 'RENAMING: %r' % rename_id, new_name

    mongo_db.users.update({
        '_id': rename_id,
    }, {'$set': {
        'name': new_name,
    }})

print 'EXIT'
