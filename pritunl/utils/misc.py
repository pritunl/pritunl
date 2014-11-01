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

def now():
    return settings.local.mongo_time + (
        datetime.datetime.utcnow() - settings.local.mongo_time_start)

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

def rmtree(path):
    for _ in xrange(8):
        try:
            subprocess.check_call(['rm', '-rf', path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return
        except subprocess.CalledProcessError:
            time.sleep(0.01)
    raise

def filter_str(in_str):
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in NAME_SAFE_CHARS)

def get_cert_block(cert_data):
    start_index = cert_data.index('-----BEGIN CERTIFICATE-----')
    end_index = cert_data.index('-----END CERTIFICATE-----') + 25
    return cert_data[start_index:end_index]

def get_temp_path():
    return os.path.join(settings.conf.temp_path, uuid.uuid4().hex)

def check_openssl():
    try:
        # Check for unpatched heartbleed
        openssl_ver = subprocess.check_output(['openssl', 'version', '-a'])
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
