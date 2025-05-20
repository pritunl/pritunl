from pritunl import __version__

from pritunl.constants import *
from pritunl import settings

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
import hmac
import re
import queue
import urllib.request, urllib.error, urllib.parse
import json
import math
import psutil
import urllib.parse

_null = open(os.devnull, 'w')

if hasattr(sys, 'frozen'):
    _srcfile = 'logging%s__init__%s' % (os.sep, __file__[-4:])
elif __file__[-4:].lower() in ('.pyc', '.pyo'):
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

PyQueue = queue.Queue
PyPriorityQueue = queue.PriorityQueue

def _now(ntp_time):
    start_time, sync_time = ntp_time
    return sync_time + (time.time() - start_time)

def now():
    return datetime.datetime.utcfromtimestamp(time.time())

def time_now():
    return time.time()

def time_diff(timestamp, ttl):
    return abs(now().timestamp() - timestamp.timestamp()) < ttl

def sync_time():
    pass

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

def _get_version_doc():
    if settings.conf.mongodb_uri:
        prefix = settings.conf.mongodb_collection_prefix or ''
        client = pymongo.MongoClient(settings.conf.mongodb_uri,
            connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
        database = client.get_default_database()
        settings_db = getattr(database, prefix + 'settings')
        doc = settings_db.find_one({
            '_id': 'version',
        })

        if doc:
            return doc

    return {}

def get_db_ver(default=True):
    return _get_version_doc().get('version') or (
        __version__ if default else None)

def get_min_db_ver(default=True):
    return _get_version_doc().get('version_min') or (
        '1.24.0.0' if default else None)

def get_db_ver_int():
    return get_int_ver(get_db_ver())

def get_min_db_ver_int():
    return get_int_ver(get_min_db_ver())

def set_db_ver(version, version_min=None):
    from pritunl import logger

    db_version = get_db_ver(False)
    db_min_version = get_min_db_ver(False)

    if (version != db_version or MIN_DATABASE_VER != db_min_version) and \
            db_version:
        logger.info('Setting db version', 'utils',
            cur_ver=db_version,
            new_ver=version,
            cur_min_ver=db_min_version,
            new_min_ver=MIN_DATABASE_VER,
        )

    update_doc = {
        '$set': {
            'version': version,
        },
    }
    if version_min:
        update_doc['$set']['version_min'] = version_min

    prefix = settings.conf.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(settings.conf.mongodb_uri,
        connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
    database = client.get_default_database()

    db_collections = database.list_collection_names()
    if 'authorities' in db_collections:
        raise TypeError('Cannot connect to a Pritunl Zero database')

    settings_db = getattr(database, prefix + 'settings')
    settings_db.update_one({
        '_id': 'version',
    }, update_doc, upsert=True)

    return version

def check_output(*args, **kwargs):
    if 'stdout' in kwargs or 'stderr' in kwargs:
        raise ValueError('Output arguments not allowed, it will be overridden')

    try:
        ignore_states = kwargs.pop('ignore_states')
    except KeyError:
        ignore_states = None

    process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        *args, **kwargs)

    stdoutdata, stderrdata = process.communicate()
    return_code = process.poll()

    stdoutdata = stdoutdata.decode()
    stderrdata = stderrdata.decode()

    if return_code:
        cmd = kwargs.get('args', args[0])

        if ignore_states:
            for ignore_state in ignore_states:
                if ignore_state in stdoutdata or ignore_state in stderrdata:
                    return stdoutdata

        raise subprocess.CalledProcessError(
            return_code, cmd, output=stdoutdata)

    return stdoutdata

def check_output_logged(*args, **kwargs):
    if 'stdout' in kwargs or 'stderr' in kwargs:
        raise ValueError('Output arguments not allowed, it will be overridden')

    try:
        ignore_states = kwargs.pop('ignore_states')
    except KeyError:
        ignore_states = None

    try:
        com_input = kwargs.pop('input')
        stdin = subprocess.PIPE
    except KeyError:
        com_input = None
        stdin = None

    process = subprocess.Popen(
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=stdin,
        *args, **kwargs)

    if com_input:
        com_input = com_input.encode()

    stdoutdata, stderrdata = process.communicate(input=com_input)
    return_code = process.poll()

    stdoutdata = stdoutdata.decode()
    stderrdata = stderrdata.decode()

    if return_code:
        from pritunl import logger
        cmd = kwargs.get('args', args[0])

        if ignore_states:
            for ignore_state in ignore_states:
                if ignore_state in stdoutdata or ignore_state in stderrdata:
                    return stdoutdata

        logger.error('Popen returned error exit code', 'utils',
            cmd=cmd,
            return_code=return_code,
            stdout=stdoutdata,
            stderr=stderrdata,
        )

        raise subprocess.CalledProcessError(
            return_code, cmd, output=stdoutdata)

    return stdoutdata

def check_call_silent(*args, **kwargs):
    if 'stdout' in kwargs or 'stderr' in kwargs:
        raise ValueError('Output arguments not allowed, it will be overridden')

    process = subprocess.Popen(stdout=_null, stderr=_null, *args, **kwargs)
    return_code = process.wait()

    if return_code:
        cmd = kwargs.get('args', args[0])
        raise subprocess.CalledProcessError(return_code, cmd)

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
    for i in range(8):
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
    if in_str is not None:
        in_str = str(in_str)
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in NAME_SAFE_CHARS)

def filter_base64(in_str):
    if in_str is not None:
        in_str = str(in_str)
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in BASE64_SAFE_CHARS)

def filter_unicode(in_str):
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in NAME_SAFE_CHARS)

def filter_str2(in_str):
    if in_str is not None:
        in_str = str(in_str)
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in NAME_SAFE_CHARS2)

def filter_path(in_str):
    if in_str is not None:
        in_str = str(in_str)
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in PATH_SAFE_CHARS)

def generate_secret():
    return generate_secret_len(32)

def generate_secret_len(n):
    l = int(n*1.3)
    for i in range(10):
        x = re.sub(r'[\W_]+', '', base64.b64encode(
            os.urandom(l)).decode())[:n]
        if len(x) == n:
            return x
    raise ValueError('Failed to generate secret')

def generate_random_mac():
    random_digits = [random.choice('0123456789ABCDEF') for _ in range(10)]
    return '02:' + ':'.join(
        [''.join(random_digits[i:i+2]) for i in range(0, 10, 2)])

def generate_otp_secret():
    sha_hash = hashlib.sha512()
    sha_hash.update(os.urandom(8192))
    byte_hash = sha_hash.digest()

    for _ in range(6):
        sha_hash = hashlib.sha512()
        sha_hash.update(byte_hash)
        byte_hash = sha_hash.digest()

    return base64.b32encode(byte_hash).decode()[:settings.user.otp_secret_len]

def get_cert_block(cert_data):
    start_index = cert_data.index('-----BEGIN CERTIFICATE-----')
    end_index = cert_data.index('-----END CERTIFICATE-----') + 25
    return cert_data[start_index:end_index]

def get_temp_path():
    if not os.path.isdir(settings.conf.temp_path):
        os.makedirs(settings.conf.temp_path)

    return os.path.join(settings.conf.temp_path, uuid.uuid4().hex)

def check_openssl():
    return True

def check_iptables_wait():
    try:
        subprocess.check_call(['iptables', '--wait', '-L', '-n'],
            stdout=_null, stderr=_null)
        return True
    except:
        pass
    return False

def roundrobin(*iterables):
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = itertools.cycle(iter(it).__next__ for it in iterables)
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

    for _ in range(100):
        try:
            process.send_signal(signal.SIGINT)
        except OSError as error:
            if error.errno != 3:
                raise
        for _ in range(4):
            if process.poll() is not None:
                terminated = True
                break
            time.sleep(0.0025)
        if terminated:
            break

    if not terminated:
        for _ in range(10):
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

def const_compare(x, y):
    return hmac.compare_digest(x, y)

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
    s = re.sub(r'[\W_]+', '', base64.b64encode(
        os.urandom(int(
            length * (1.5 if length > 10 else 2)))).decode())[:length]
    if len(s) != length:
        return rand_str(length)
    return s

def rand_str_ne(length):
    s = re.sub(r'[\W_1lLiIoO0]+', '', base64.b64encode(
        os.urandom(int(
            length * (2 if length > 10 else 3)))).decode())[:length]
    if len(s) != length:
        return rand_str(length)
    return s

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

def base64raw_decode(data):
    return base64.b64decode(data.encode() + b'=' * (-len(data) % 4))

def base64raw_encode(data):
    return base64.b64encode(data).strip(b'=').decode('utf8')

def sync_public_ip(attempts=1, timeout=5):
    from pritunl import logger

    for i in range(attempts):
        url = settings.app.public_ip_server
        if settings.app.dedicated:
            url = settings.app.dedicated + '/ip'

        if i:
            time.sleep(3)
            logger.info('Retrying get public ip address', 'utils')
        try:
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'pritunl')
            response = urllib.request.urlopen(request, timeout=timeout)
            settings.local.public_ip = str(json.load(response)['ip'])
            break
        except:
            pass

    if not settings.app.dedicated:
        try:
            request = urllib.request.Request(
                settings.app.public_ip6_server)
            request.add_header('User-Agent', 'pritunl')
            response = urllib.request.urlopen(request, timeout=timeout)
            settings.local.public_ip6 = str(json.load(response)['ip'])
        except:
            pass

        if not settings.local.public_ip:
            logger.warning('Failed to get public ip address', 'utils')

def ping(address, timeout=1):
    start = time.time()
    code = subprocess.call(['ping', '-c', '1', '-W',
            str(math.ceil(timeout)), address],
        stdout=_null, stderr=_null)
    runtime = (time.time() - start)
    if code != 0:
        return None
    return runtime

def get_process_cpu_mem():
    proc = psutil.Process(os.getpid())
    return proc.cpu_percent(interval=0.5), proc.memory_percent()

def redirect(location, code=302):
    location = urllib.parse.urljoin(get_url_root(), location)
    return flask.redirect(location, code)

def get_url_root():
    url_root = flask.request.headers.get('PR-Forwarded-Url')
    url_root = url_root.replace('http://', 'https://', 1)

    if url_root[-1] == '/':
        url_root = url_root[:-1]

    return url_root

def check_openvpn_ver():
    try:
        process = subprocess.Popen(['openvpn', '--version'],
            stdout=subprocess.PIPE)
        output, _ = process.communicate()
        output = output.decode().split()[1].strip()

        version = [int(x) for x in output.split('.')]

        if version[0] > 2:
            return True

        if version[0] == 2 and version[1] > 3:
            return True

        if version[0] == 2 and version[1] == 3 and version[2] > 2:
            return True
    except:
        from pritunl import logger
        logger.exception('Failed to check openvpn version', 'utils')

    return False

def systemd_available():
    for proc in psutil.process_iter():
        if proc.name() == 'systemd':
            return True
    return False

def systemd_start(service):
    check_output_logged([
        'systemctl', 'restart', service,
    ])

def systemd_stop(service):
    check_output_logged([
        'systemctl', 'stop', service,
    ])

def systemd_stop_silent(service):
    check_call_silent([
        'systemctl', 'stop', service,
    ])

def systemd_reload():
    check_output_logged([
        'systemctl', 'daemon-reload',
    ])

def systemd_is_active(service):
    process = subprocess.Popen(['systemctl', 'is-active', '--quiet', service])
    return_code = process.wait()
    if return_code == 0:
        return True
    return False
