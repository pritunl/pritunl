from pritunl import __version__

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo

import subprocess
import time
import datetime
import itertools
import random
import uuid
import os
import bson
import signal
import flask
import sys
import json
import pymongo
import hashlib
import base64
import re

if hasattr(sys, 'frozen'):
    _srcfile = 'logging%s__init__%s' % (os.sep, __file__[-4:])
elif __file__[-4:].lower() in ('.pyc', '.pyo'):
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

def now():
    return settings.local.mongo_time + (
        datetime.datetime.utcnow() - settings.local.mongo_time_start)

def get_int_ver(version):
    ver = re.findall(r'\d+', version)

    if 'alpha' in version:
        ver[3] = str(int(ver[3]) + 1000)
    elif 'beta' in version:
        ver[3] = str(int(ver[3]) + 2000)
    elif 'rc' in version:
        ver[3] = str(int(ver[3]) + 3000)
    elif len(ver) > 3:
        ver[3] = ver[3].zfill(4)
    else:
        ver.append('0000')

    return int(''.join([x.zfill(2) for x in ver]))

def get_db_ver():
    prefix = settings.conf.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(settings.conf.mongodb_uri,
        connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
    database = client.get_default_database()
    settings_db = getattr(database, prefix + 'settings')
    doc = settings_db.find_one({
        '_id': 'version',
    }) or {}

    version = doc.get('version')
    if version:
        return version

    if not version and settings.conf.data_path:
        path = os.path.join(settings.conf.data_path, 'version')
        if os.path.exists(path):
            with open(path, 'r') as ver_file:
                return ver_file.read().strip()

    return __version__

def get_db_ver_int():
    version = get_db_ver()
    if version:
        return get_int_ver(version)

def set_db_ver(version):
    prefix = settings.conf.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(settings.conf.mongodb_uri,
        connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
    database = client.get_default_database()
    settings_db = getattr(database, prefix + 'settings')
    doc = settings_db.update({
        '_id': 'version',
    }, {
        'version': version,
    }, upsert=True)
    return doc.get('version')

def check_output_logged(*args, **kwargs):
    if 'stdout' in kwargs or 'stderr' in kwargs:
        raise ValueError('Output arguments not allowed, it will be overridden')

    process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        *args, **kwargs)

    stdoutdata, stderrdata = process.communicate()
    return_code = process.poll()

    if return_code:
        from pritunl import logger
        cmd = kwargs.get('args', args[0])

        logger.error('Popen returned error exit code', 'utils',
            cmd=cmd,
            return_code=return_code,
            stdout=stdoutdata,
            stderr=stderrdata,
        )

        raise subprocess.CalledProcessError(
            return_code, cmd, output=stdoutdata)

    return stdoutdata

def sync_time():
    collection = mongo.get_collection('time_sync')

    nounce = bson.ObjectId()
    collection.insert({
        'nounce': nounce,
    }, manipulate=False)

    settings.local.mongo_time_start = datetime.datetime.utcnow()

    doc = collection.find_one({
        'nounce': nounce,
    })
    settings.local.mongo_time = doc['_id'].generation_time.replace(tzinfo=None)

    collection.remove(doc['_id'])

def find_caller():
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back

    if f is not None:
        f = f.f_back
    rv = "(unknown file)", 0, "(unknown function)"

    while hasattr(f, "f_code"):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)

        if filename == _srcfile:
            f = f.f_back
            continue

        rv = (co.co_filename, f.f_lineno, co.co_name)
        break

    return rv

def rmtree(path):
    for i in xrange(8):
        try:
            check_output_logged(['rm', '-rf', path])
            return
        except subprocess.CalledProcessError:
            if i == 7:
                from pritunl import logger
                logger.exception('Failed to rm files', 'utils',
                    path=path,
                )
            time.sleep(0.01)

def filter_str(in_str):
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in NAME_SAFE_CHARS)

def generate_secret():
    return re.sub(r'[\W_]+', '', base64.b64encode(os.urandom(64)))[:32]

def generate_otp_secret():
    sha_hash = hashlib.sha512()
    sha_hash.update(os.urandom(8192))
    byte_hash = sha_hash.digest()

    for _ in xrange(6):
        sha_hash = hashlib.sha512()
        sha_hash.update(byte_hash)
        byte_hash = sha_hash.digest()

    return base64.b32encode(byte_hash)[:settings.user.otp_secret_len]

def get_cert_block(cert_data):
    start_index = cert_data.index('-----BEGIN CERTIFICATE-----')
    end_index = cert_data.index('-----END CERTIFICATE-----') + 25
    return cert_data[start_index:end_index]

def get_temp_path():
    return os.path.join(settings.conf.temp_path, uuid.uuid4().hex)

def check_openssl():
    try:
        # Check for unpatched heartbleed
        openssl_ver = check_output_logged(['openssl', 'version', '-a'])
        version, build_date = openssl_ver.split('\n')[0:2]

        build_date = build_date.replace('built on:', '').strip()
        build_date = build_date.split()
        build_date = ' '.join([build_date[1],
            build_date[2].zfill(2), build_date[5]])
        build_date = datetime.datetime.strptime(build_date, '%b %d %Y').date()

        if version in OPENSSL_HEARTBLEED and \
                build_date < OPENSSL_HEARTBLEED_BUILD_DATE:
            return False
    except:
        pass
    return True

def roundrobin(*iterables):
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = itertools.cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = itertools.cycle(itertools.islice(nexts, pending))

def random_name():
    return '%s-%s-%s' % (
        random.choice(RANDOM_ONE),
        random.choice(RANDOM_TWO),
        random.randint(1000, 9999),
    )

def stop_process(process):
    terminated = False

    for _ in xrange(100):
        try:
            process.send_signal(signal.SIGINT)
        except OSError as error:
            if error.errno != 3:
                raise
        for _ in xrange(4):
            if process.poll() is not None:
                terminated = True
                break
            time.sleep(0.0025)
        if terminated:
            break

    if not terminated:
        for _ in xrange(10):
            if process.poll() is not None:
                terminated = True
                break
            try:
                process.send_signal(signal.SIGKILL)
            except OSError as error:
                if error.errno != 3:
                    raise
            time.sleep(0.01)

    return terminated

def response(data=None, status_code=None):
    response = flask.Response(response=data,
        mimetype='text/html; charset=utf-8')
    response.headers.add('Cache-Control',
        'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', 0)
    if status_code is not None:
        response.status_code = status_code
    return response

def styles_response(etag, last_modified, data):
    response = flask.Response(response=data, mimetype='text/css')
    if settings.conf.static_cache:
        response.headers.add('Cache-Control', 'max-age=43200, public')
        response.headers.add('ETag', '"%s"' % etag)
    else:
        response.headers.add('Cache-Control',
            'no-cache, no-store, must-revalidate')
        response.headers.add('Pragma', 'no-cache')
        response.headers.add('Expires', 0)
    response.headers.add('Last-Modified', last_modified)
    return response
