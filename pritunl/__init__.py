from constants import *
__title__ = APP_NAME
__version__ = '0.10.3'
__author__ = 'Zachary Huff'
__license__ = 'AGPL'
__copyright__ = 'Copyright 2013 Zachary Huff'
import threading

openssl_lock = threading.Lock()

from app_server import AppServer
app_server = AppServer()
