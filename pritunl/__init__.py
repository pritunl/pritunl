from pritunl.constants import *

__title__ = APP_NAME
__version__ = '0.10.12'
__author__ = 'Pritunl'
__license__ = 'Custom'
__copyright__ = 'Copyright 2013-2014 Pritunl'
conf_path = DEFAULT_CONF_PATH

def init_server(path=None):
    if path:
        global conf_path
        conf_path = path

    from pritunl import app
    from pritunl.app_server import app_server
    app_server.app = app.app

    from pritunl import setup
    setup.setup_all()

    app_server.run_server()
