from pritunl import __version__

from pritunl.constants import *
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
import pymongo
import hashlib
import base64
import re
import Queue

if hasattr(sys, 'frozen'):
    _srcfile = 'logging%s__init__%s' % (os.sep, __file__[-4:])
elif __file__[-4:].lower() in ('.pyc', '.pyo'):
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

PyQueue = Queue.Queue
PyPriorityQueue = Queue.PriorityQueue

def ObjectId(oid=None):
    if oid is None or len(oid) != 32:
        try:
            return bson.ObjectId(oid)
        except:
            from pritunl import logger
            logger.exception('Failed to convert object id', 'utils',
                object_id=oid,
            )
    return oid

def _now(mongo_time):
    mongo_time_start, mongo_time_cur = mongo_time
    return mongo_time_cur + (datetime.datetime.utcnow() - mongo_time_start)

def now():
    return _now(settings.local.mongo_time)

def time_now():
    return int((now() - datetime.datetime(1970, 1, 1)).total_seconds())

def rand_sleep():
    time.sleep(random.randint(0, 25) / 1000.)

def get_int_ver(version):
    ver = re.findall(r'\d+', version)

    if 'snapshot' in version:
        pass
    elif 'alpha' in version:
        ver[-1] = str(int(ver[-1]) + 1000)
    elif 'beta' in version:
        ver[-1] = str(int(ver[-1]) + 2000)
    elif 'rc' in version:
        ver[-1] = str(int(ver[-1]) + 3000)
    else:
        ver[-1] = str(int(ver[-1]) + 4000)

    return int(''.join([x.zfill(4) for x in ver]))

def get_db_ver():
    if settings.conf.mongodb_uri:
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

    return __version__

def get_db_ver_int():
    version = get_db_ver()
    if version:
        return get_int_ver(version)

def set_db_ver(version):
    from pritunl import logger

    db_version = get_db_ver()

    if version != db_version:
        logger.info('Setting db version', 'utils',
            cur_ver=db_version,
            new_ver=version,
        )

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
    nounce = None
    doc = {}

    try:
        collection = mongo.get_collection('time_sync')

        nounce = ObjectId()
        collection.insert({
            'nounce': nounce,
        }, manipulate=False)

        mongo_time_start = datetime.datetime.utcnow()
        cur_mongo_time = settings.local.mongo_time

        doc = collection.find_one({
            'nounce': nounce,
        })
        mongo_time = doc['_id'].generation_time.replace(tzinfo=None)

        settings.local.mongo_time = (mongo_time_start, mongo_time)

        if cur_mongo_time:
            time_diff = abs(_now(cur_mongo_time) - now())
            if time_diff > datetime.timedelta(milliseconds=1000):
                from pritunl import logger
                logger.error(
                    'Unexpected time deviation from mongodb', 'utils',
                    deviation=str(time_diff),
                )

        collection.remove(doc['_id'])
    except:
        from pritunl import logger

        logger.exception('Failed to sync time',
            nounce=nounce,
            doc_id=doc.get('id'),
        )
        raise

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

def check_iptables_wait():
    try:
        subprocess.check_call(['iptables', '--wait', '-L', '-n'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        pass
    return False

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

def rand_str(length):
    return re.sub(r'[\W_]+', '', base64.b64encode(
        os.urandom(length * 2)))[:length]

prime32 = 16777619
prime64 = 1099511628211
uint32_max = 2 ** 32
uint64_max = 2 ** 64

def fnv32a(s):
    hval = 2166136261
    for x in s:
        hval ^= ord(x)
        hval = (hval * prime32) % uint32_max
    return hval

def fnv64a(s):
    hval = 14695981039346656037
    for x in s:
        hval ^= ord(x)
        hval = (hval * prime64) % uint64_max
    return hval
