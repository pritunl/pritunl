from pritunl.utils.misc import ObjectId, filter_str

import flask

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
    return ObjectId(flask.request.json[key])

def json_opt_oid(key):
    val = flask.request.json.get(key)
    return None if val is None else ObjectId(val)

def session_int(key):
    return int(flask.session.get(key))

def session_opt_int(key):
    val = flask.session.get(key)
    return None if val is None else int(val)

def session_str(key):
    return str(flask.session.get(key) or '')

def session_opt_str(key):
    val = flask.session.get(key)
    return None if val is None else str(val)
