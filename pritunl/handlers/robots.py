from pritunl.constants import *
from pritunl import utils
from pritunl import app
from pritunl import auth

@app.app.route('/robots.txt', methods=['GET'])
@auth.open_auth
def robots_get():
    return utils.response(data=ROBOTS)
