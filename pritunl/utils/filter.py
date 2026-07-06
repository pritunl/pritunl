from pritunl.utils.misc import filter_str
from pritunl import database

import flask
import re
import ipaddress
import urllib.parse

_domain_re = re.compile(
    r'^(?=.{1,253}$)'
    r'([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*'
    r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$'
)

def clean_domain(in_str):
    if in_str is None:
        return None
    in_str = str(in_str).strip()
    if not in_str:
        return None

    if '://' not in in_str:
        try:
            if ipaddress.ip_address(in_str).version == 6:
                in_str = '[%s]' % in_str
        except ValueError:
            pass
        in_str = 'http://' + in_str

    try:
        parsed = urllib.parse.urlsplit(in_str)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None

    if not hostname:
        return None
    hostname = hostname.lower()

    is_ipv6 = False
    try:
        is_ipv6 = ipaddress.ip_address(hostname).version == 6
    except ValueError:
        if not _domain_re.match(hostname):
            return None

    host = '[%s]' % hostname if is_ipv6 else hostname

    if port is not None:
        return '%s:%d' % (host, port)
    return host

def json_str(key):
    return str(flask.request.json[key])

def json_opt_str(key):
    val = flask.request.json.get(key)
    return None if val is None else str(val)

def json_filter_str(key):
    return filter_str(flask.request.json[key])

def json_opt_filter_str(key):
    val = flask.request.json.get(key)
    return None if val is None else filter_str(val)

def json_int(key):
    return int(flask.request.json[key])

def json_opt_int(key):
    val = flask.request.json.get(key)
    return None if val is None else int(val)

def json_float(key):
    return float(flask.request.json[key])

def json_opt_float(key):
    val = flask.request.json.get(key)
    return None if val is None else float(val)

def json_bool(key):
    return bool(flask.request.json[key])

def json_opt_bool(key):
    val = flask.request.json.get(key)
    return None if val is None else bool(val)

def json_oid(key):
    return database.ObjectId(flask.request.json[key])

def json_opt_oid(key):
    val = flask.request.json.get(key)
    return None if val is None else database.ObjectId(val)

def session_int(key):
    return int(flask.session.get(key))

def session_opt_int(key):
    val = flask.session.get(key)
    return None if val is None else int(val)

def session_str(key):
    return str(flask.session.get(key) or '')

def session_opt_str(key):
    val = flask.session.get(key)
    if isinstance(val, bytes):
        val = val.decode()
    return None if val is None else str(val)
