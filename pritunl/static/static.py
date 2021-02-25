from pritunl.static.utils import *
from pritunl.cachelocal import cache_db

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import settings

import gzip
import io
import shutil
import os
import datetime
import mimetypes
import flask
import werkzeug.http

class StaticFile(object):
    def __init__(self, root, path, cache=True, gzip=True):
        path = '/'.join([x for x in path.split('/') if x and x != '..'])
        path = os.path.normpath(os.path.join(root, path))

        if os.path.commonprefix([root, path]) != root:
            raise InvalidStaticFile(
                'Static path is not a prefix of root path',
                {'path': path},
            )

        if os.path.splitext(path)[1] not in STATIC_FILE_EXTENSIONS:
            raise InvalidStaticFile(
                'Static path file extension is invalid',
                {'path': path},
            )

        self.path = path
        self.cache = cache
        self.gzip = gzip
        self.data = None
        self.mime_type = None
        self.last_modified = None
        self.etag = None
        self.load_file()

    def get_cache_key(self):
        return 'file_%s' % self.path

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
        if settings.conf.static_cache and cache_db.exists(
                self.get_cache_key()):
            self.get_cache()
            return

        if not os.path.isfile(self.path):
            if settings.conf.static_cache:
                self.set_cache()
            return

        file_basename = os.path.basename(self.path)
        file_mtime = datetime.datetime.utcfromtimestamp(
            os.path.getmtime(self.path))
        file_size = int(os.path.getsize(self.path))

        if self.gzip:
            gzip_data = io.BytesIO()
            with open(self.path, 'rb') as static_file, \
                    gzip.GzipFile(fileobj=gzip_data, mode='wb') as gzip_file:
                shutil.copyfileobj(static_file, gzip_file)
            self.data = gzip_data.getvalue()
        else:
            with open(self.path, 'r') as static_file:
                self.data = static_file.read()

        self.mime_type = mimetypes.guess_type(file_basename)[0] or \
            'text/plain'
        self.last_modified = werkzeug.http.http_date(file_mtime)
        self.etag = generate_etag(file_basename, file_size, file_mtime)
        if settings.conf.static_cache:
            self.set_cache()

    def get_response(self):
        if not self.last_modified:
            flask.abort(404)
        response = flask.Response(response=self.data, mimetype=self.mime_type)

        if self.gzip:
            response.headers.add('Content-Encoding', 'gzip')

        if settings.conf.static_cache and self.cache:
            response.headers.add('Cache-Control',
                'max-age=%s, public' % settings.app.static_cache_time)
            response.headers.add('ETag', '"%s"' % self.etag)
        else:
            response.headers.add('Cache-Control',
                'no-cache, no-store, must-revalidate')
            response.headers.add('Pragma', 'no-cache')
            response.headers.add('Expires', 0)

        response.headers.add('Last-Modified', self.last_modified)
        return response
