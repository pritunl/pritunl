from constants import *
from pritunl import app_server
from cache import cache_db
from werkzeug.http import http_date
import os
import sys
import zlib
import time
import datetime
import mimetypes
import flask

class StaticFile:
    def __init__(self, path, cache=True):
        self.path = path
        self.cache = cache
        self.data = None
        self.mime_type = None
        self.last_modified = None
        self.etag = None
        self.load_file()

    def get_cache_key(self):
        return 'file_%s' % self.path

    def generate_etag(self, file_name, file_size, mtime):
        file_name = file_name.encode(sys.getfilesystemencoding())
        return 'wzsdm-%d-%s-%s' % (
            time.mktime(mtime.timetuple()),
            file_size,
            zlib.adler32(file_name) & 0xffffffff,
        )

    def set_cache(self):
        cache_db.dict_set(self.get_cache_key(), 'data', self.data or '')
        cache_db.dict_set(self.get_cache_key(), 'mime_type',
            self.mime_type or '')
        cache_db.dict_set(self.get_cache_key(), 'last_modified',
            self.last_modified)
        cache_db.dict_set(self.get_cache_key(), 'etag', self.etag or '')

    def get_cache(self):
        self.data = cache_db.dict_get(self.get_cache_key(), 'data')
        self.mime_type = cache_db.dict_get(self.get_cache_key(), 'mime_type')
        self.last_modified = cache_db.dict_get(self.get_cache_key(),
            'last_modified')
        self.etag = cache_db.dict_get(self.get_cache_key(), 'etag')

    def load_file(self):
        if cache_db.exists(self.get_cache_key()):
            self.get_cache()
            return

        if not os.path.isfile(self.path):
            self.set_cache()
            return

        file_basename = os.path.basename(self.path)
        file_mtime = datetime.datetime.utcfromtimestamp(
            os.path.getmtime(self.path))
        file_size = int(os.path.getsize(self.path))

        with open(self.path, 'r') as fd:
            self.data = fd.read()

        self.mime_type = mimetypes.guess_type(file_basename)[0] or 'text/plain'
        self.last_modified = http_date(file_mtime)
        self.etag = self.generate_etag(file_basename, file_size, file_mtime)
        self.set_cache()

    def get_response(self):
        if not self.last_modified:
            flask.abort(404)
        response = flask.Response(response=self.data, mimetype=self.mime_type)
        if self.cache:
            response.headers.add('Cache-Control',
                'max-age=%s, public' % STATIC_CACHE_TIME)
            response.headers.add('ETag', '"%s"' % self.etag)
        else:
            response.headers.add('Cache-Control',
                'no-cache, no-store, must-revalidate')
            response.headers.add('Pragma', 'no-cache')
            response.headers.add('Expires', 0)
        response.headers.add('Last-Modified', self.last_modified)
        return response
