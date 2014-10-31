from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

from pritunl import mongo
from pritunl import utils

import pymongo

def get_log_lines():
    collection = mongo.get_collection('log')

    output = collection.aggregate([
        {'$sort': {
            'timestamp': pymongo.ASCENDING,
        }},
        {'$group': {
            '_id': None,
            'output': {'$push': '$message'},
        }},
    ])['result']

    if output:
        output = output[0]['output']

    return '\n'.join(output)
