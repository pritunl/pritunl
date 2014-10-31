from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

from pritunl import mongo
from pritunl import utils

import pymongo
import tarfile
import os
import collections

class LogView(object):
    def __init__(self):
        self.colors = (x for x in BASH_COLORS)
        self.host_colors = collections.defaultdict(lambda: self.get_color())
        self.log_colors = {
            'DEBUG': '90',
            'INFO': '94',
            'WARNING': '93',
            'ERROR': '91',
            'CRITICAL': '95',
        }

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('logs')

    def get_color(self):
        try:
            return self.colors.next()
        except StopIteration:
            self.colors = (x for x in BASH_COLORS)
            return get_color()

    def format_line(self, line):
        if line[0] == '[':
            try:
                line_split = line.split(']', 3)
                log_host = line_split[0][1:]
                log_time = line_split[1][1:]
                log_level = line_split[2][1:]
                log_msg = line_split[3]

                return '\033[1;%sm[%s]\033[0m\033[1m[%s]\033' +
                        '[0m\033[0;%sm[%s]\033[0m%s' % (
                    self.host_colors[log_host], log_host,
                    log_time,
                    self.log_colors.get(log_level), log_level,
                    log_msg,
                )
            except:
               pass
        return line

    def get_log_lines(self, formatted=True):
        collection = mongo.get_collection('logs')

        messages = collection.aggregate([
            {'$sort': {
                'timestamp': pymongo.ASCENDING,
            }},
            {'$group': {
                '_id': None,
                'messages': {'$push': '$message'},
            }},
        ])['result']

        if messages:
            messages = messages[0]['messages']

        if formatted:
            output = ''
            for msg in messages:
                output += self.format_line(msg) + '\n'
            return output
        else:
            return '\n'.join(output)

    def tail_log_lines(self, formatted=True):
        cursor_id = self.collection.find().sort(
            '$natural', pymongo.DESCENDING)[100]['_id']

        spec = {
            '_id': {'$gt': cursor_id},
        }
        cursor = collection.find(spec, tailable=True,
            await_data=True).sort('$natural', pymongo.ASCENDING)

        while cursor.alive:
            for doc in cursor:
                cursor_id = doc['_id']

                if formatted:
                    yield self.format_line(doc['message'])
                else:
                    yield doc['message']

    def archive_log(self, archive_path):
        temp_path = utils.get_temp_path()
        if os.path.isdir(archive_path):
            archive_path = os.path.join(
                archive_path, LOG_ARCHIVE_NAME + '.tar')
        output_path = os.path.join(temp_path, LOG_ARCHIVE_NAME)

        try:
            os.makedirs(temp_path)
            tar_file = tarfile.open(archive_path, 'w')
            try:
                with open(output_path, 'w') as log_file:
                    log_file.write(self.get_log_lines(False))
                tar_file.add(output_path, arcname=LOG_ARCHIVE_NAME)
            finally:
                tar_file.close()
        finally:
            utils.rmtree(temp_path)

        return archive_path
