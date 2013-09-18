import flask
import json

def jsonify(data=None, status_code=None):
    if not isinstance(data, basestring):
        data = json.dumps(data)

    callback = flask.request.args.get('callback', False)
    if callback:
        data = '%s(%s)' % (callback, data)
        mimetype = 'application/javascript'
    else:
        mimetype = 'application/json'

    response = flask.Response(response=data, mimetype=mimetype)

    if status_code is not None:
        response.status_code = status_code

    return response
