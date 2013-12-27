import flask
import json

def jsonify(data=None, status_code=None):
    if not isinstance(data, basestring):
        data = json.dumps(data)
    response = flask.Response(response=data, mimetype='application/json')
    if status_code is not None:
        response.status_code = status_code
    return response
