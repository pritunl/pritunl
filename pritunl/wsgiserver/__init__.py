# Fork of cherrpy wsgiserver to fix HTTPConnection socket error with ssl

__all__ = ['HTTPRequest', 'HTTPConnection', 'HTTPServer',
           'SizeCheckWrapper', 'KnownLengthRFile', 'ChunkedRFile',
           'MaxSizeExceeded', 'NoSSLError', 'FatalSSLAlert',
           'WorkerThread', 'ThreadPool', 'SSLAdapter',
           'CherryPyWSGIServer',
           'Gateway', 'WSGIGateway', 'WSGIGateway_10', 'WSGIGateway_u0',
           'WSGIPathInfoDispatcher', 'get_ssl_adapter_class']

import sys
from wsgiserver2 import *
