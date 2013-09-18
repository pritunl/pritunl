from pritunl.constants import *
from pritunl import server

@server.app.route('/test', methods=['GET'])
def test_get():
    return 'test'
