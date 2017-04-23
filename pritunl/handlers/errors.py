from pritunl import app
from pritunl import auth

@app.app.errorhandler(400)
@auth.open_auth
def error_400(_):
    return '400: Bad Request', 400

@app.app.errorhandler(401)
@auth.open_auth
def error_401(_):
    return '401: Unauthorized', 401

@app.app.errorhandler(403)
@auth.open_auth
def error_403(_):
    return '403: Forbidden', 403

@app.app.errorhandler(404)
@auth.open_auth
def error_404(_):
    return '404: Not Found', 404

@app.app.errorhandler(405)
@auth.open_auth
def error_405(_):
    return '405: Not Allowed', 405

@app.app.errorhandler(406)
@auth.open_auth
def error_406(_):
    return '406: Not Acceptable', 406

@app.app.errorhandler(408)
@auth.open_auth
def error_408(_):
    return '408: Request Timeout', 408

@app.app.errorhandler(409)
@auth.open_auth
def error_409(_):
    return '409: Conflict', 409

@app.app.errorhandler(410)
@auth.open_auth
def error_410(_):
    return '410: Gone', 410

@app.app.errorhandler(411)
@auth.open_auth
def error_411(_):
    return '411: Length Required', 411

@app.app.errorhandler(412)
@auth.open_auth
def error_412(_):
    return '412: Precondition Failed', 412

@app.app.errorhandler(413)
@auth.open_auth
def error_413(_):
    return '413: Payload Too Large', 413

@app.app.errorhandler(414)
@auth.open_auth
def error_414(_):
    return '414: URI Too Long', 414

@app.app.errorhandler(415)
@auth.open_auth
def error_415(_):
    return '415: Unsupported Media Type', 415

@app.app.errorhandler(416)
@auth.open_auth
def error_416(_):
    return '416: Range Not Satisfiable', 416

@app.app.errorhandler(417)
@auth.open_auth
def error_417(_):
    return '417: Expectation Failed', 417

@app.app.errorhandler(418)
@auth.open_auth
def error_418(_):
    return '418: Unknown Error', 418

@app.app.errorhandler(422)
@auth.open_auth
def error_422(_):
    return '422: Unprocessable Entity', 422

@app.app.errorhandler(428)
@auth.open_auth
def error_428(_):
    return '428: Precondition Required', 428

@app.app.errorhandler(429)
@auth.open_auth
def error_429(_):
    return '429: Too Many Requests', 429

@app.app.errorhandler(431)
@auth.open_auth
def error_431(_):
    return '431: Request Header Fields Too Large', 431

@app.app.errorhandler(500)
@auth.open_auth
def error_500(_):
    return '500: Internal Server Error', 500

@app.app.errorhandler(501)
@auth.open_auth
def error_501(_):
    return '501: Not Implemented', 501

@app.app.errorhandler(502)
@auth.open_auth
def error_502(_):
    return '502: Bad Gateway', 502

@app.app.errorhandler(503)
@auth.open_auth
def error_503(_):
    return '503: Service Unavailable', 503

@app.app.errorhandler(504)
@auth.open_auth
def error_504(_):
    return '504: Gateway Timeout', 504

@app.app.errorhandler(505)
@auth.open_auth
def error_505(_):
    return '505: HTTP Version Not Supported', 505
