from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

from pritunl import mongo
from pritunl import utils

import pymongo
import tarfile
import os

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

def archive_log(archive_path):
    temp_path = utils.get_temp_path()
    if os.path.isdir(archive_path):
        archive_path = os.path.join(archive_path, LOG_ARCHIVE_NAME + '.tar')
    output_path = os.path.join(temp_path, LOG_ARCHIVE_NAME)

    try:
        os.makedirs(temp_path)
        tar_file = tarfile.open(archive_path, 'w')
        try:
            with open(output_path, 'w') as log_file:
                log_file.write(get_log_lines())
            tar_file.add(output_path, arcname=LOG_ARCHIVE_NAME)
        finally:
            tar_file.close()
    finally:
        utils.rmtree(temp_path)

    return archive_path
