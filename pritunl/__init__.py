from pritunl import patches
from pritunl.constants import *

__title__ = 'pritunl_client'
__version__ = '0.10.12'
__author__ = 'Pritunl'
__license__ = 'Custom'
__copyright__ = 'Copyright 2013-2014 Pritunl'
conf_path = DEFAULT_CONF_PATH

def set_conf_path(path=None):
    if path:
        global conf_path
        conf_path = path

def init_server():
    from pritunl import app
    from pritunl import setup
    setup.setup_all()
    app.run_server()
