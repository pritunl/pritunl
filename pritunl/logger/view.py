from pritunl.constants import *
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
            return next(self.colors)
        except StopIteration:
            self.colors = (x for x in BASH_COLORS)
            return self.get_color()

    def format_line(self, line):
        if line[0] == '[':
            try:
                line_split = line.split(']', 3)
                log_host = line_split[0][1:]
                log_time = line_split[1][1:]
                log_level = line_split[2][1:]
                log_msg = line_split[3]

                if log_level in ('WARNING', 'ERROR', 'CRITICAL'):
                    log_msg = log_msg.replace(
                        'Process stdout:',
                        '\033[1;93mProcess stdout:\033[0m',
                    )
                    log_msg = log_msg.replace(
                        'Process stderr:',
                        '\033[1;91mProcess stderr:\033[0m',
                    )
                    log_msg = log_msg.replace(
                        'Traceback (most recent call last):',
                        '\033[1;91mTraceback (most recent call last):\033[0m',
                    )

                return ('\033[1;%sm[%s]\033[0m\033[1m[%s]\033' + \
                        '[0m\033[1;%sm[%s]\033[0m%s') % (
                    self.host_colors[log_host], log_host,
                    log_time,
                    self.log_colors.get(log_level), log_level,
                    log_msg,
                )
            except:
               pass
        return line

    def get_log_lines(self, natural=False, limit=None, formatted=True,
            reverse=False):
        limit = limit or 1024

        if natural:
            cursor = self.collection.find({}).sort(
                '$natural', pymongo.DESCENDING)
            if limit:
                cursor = cursor.limit(limit)

            messages = []
            for doc in cursor:
                messages.append(doc['message'])
        else:
            response = self.collection.aggregate([
                {'$sort': {
                    'timestamp': pymongo.DESCENDING,
                }},
                {'$limit': limit},
                {'$group': {
                    '_id': None,
                    'messages': {'$push': '$message'},
                }},
            ])

            val = None
            for val in response:
                break

            if val:
                messages = val['messages']
            else:
                messages = []

        if formatted:
            output = ''
            for i in range(len(messages) - 1, -1, -1):
                output += self.format_line(messages[i]) + '\n'
            return output.rstrip('\n')
        else:
            return '\n'.join(
                messages[::-1] if reverse else messages).rstrip('\n')

    def tail_log_lines(self, formatted=True):
        cursor = self.collection.find().sort(
            '$natural', pymongo.DESCENDING)
        cursor_count = cursor.count()

        if cursor_count > 127:
            cursor_id = cursor[127]['_id']
        else:
            cursor_id = cursor[cursor_count - 1]['_id']

        spec = {
            '_id': {'$gt': cursor_id},
        }

        cursor = self.collection.find(spec,
            cursor_type=pymongo.cursor.CursorType.TAILABLE_AWAIT).sort(
            '$natural', pymongo.ASCENDING)

        while cursor.alive:
            for doc in cursor:
                if formatted:
                    yield self.format_line(doc['message'])
                else:
                    yield doc['message']

    def archive_log(self, archive_path, natural, limit):
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
                    log_file.write(self.get_log_lines(
                        natural=natural,
                        limit=limit,
                        formatted=False
                    ))
                tar_file.add(output_path, arcname=LOG_ARCHIVE_NAME)
            finally:
                tar_file.close()
        finally:
            utils.rmtree(temp_path)

        return archive_path
