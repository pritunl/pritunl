from pritunl import patches
from pritunl.constants import *

__title__ = 'pritunl'
__version__ = '1.30.2817.44'
__author__ = 'Pritunl'
__email__ = 'contact@pritunl.com'
__license__ = 'Custom'
__copyright__ = 'Copyright 2013-2021 Pritunl <contact@pritunl.com>'
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
