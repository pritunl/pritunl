from pritunl.constants import *
import pritunl.patches
__title__ = APP_NAME
__version__ = '0.10.12'
__author__ = 'Pritunl'
__license__ = 'AGPL'
__copyright__ = 'Copyright 2013-2014 Pritunl'

from pritunl.app_server import AppServer
app_server = AppServer()
