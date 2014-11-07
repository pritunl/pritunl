from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import ipaddress
from pritunl import logger
from pritunl import host
from pritunl import utils
from pritunl import mongo
from pritunl import queue
from pritunl import transaction
from pritunl import event
from pritunl import messenger
from pritunl import organization
from pritunl import listener

import os
import signal
import time
import datetime
import subprocess
import threading
import traceback
import re
import bson
import pymongo
import random
import collections
import select
import socket

class ServerInstanceCom(object):
    def __init__(self, server, instance):
        self.server = server
        self.instance = instance
        self.sock = None
        self.socket_path = instance.management_socket_path
        self.client = None

    def client_connect(self, client):
        return True

    def parse_line(self, line):
        if self.client:
            if line == '>CLIENT:ENV,END':
                if self.client_connect(self.client):
                    self.sock.send('client-auth %s %s\nEND\n' % (
                        self.client['client_id'], self.client['key_id']))
                self.client = None
            elif line[:11] == '>CLIENT:ENV':
                env_key, env_val = line[12:].split('=', 1)
                if env_key == 'tls_id_0':
                    o_index = env_val.find('O=')
                    cn_index = env_val.find('CN=')
                    if o_index < 0 or cn_index < 0:
                        print 'error'
                    if o_index > cn_index:
                        org_id = env_val[o_index + 2:]
                        user_id = env_val[3:o_index]
                    else:
                        org_id = env_val[2:cn_index]
                        user_id = env_val[cn_index + 3:]

                    self.client['org_id'] = org_id
                    self.client['user_id'] = user_id
                elif env_key == 'IV_HWADDR':
                    self.client['mac_addr'] = env_val
                elif env_key == 'IV_SSL':
                    self.client['ssl_ver'] = env_val
                elif env_key == 'untrusted_ip':
                    self.client['remote_ip'] = env_val
                elif env_key == 'username':
                    self.client['username'] = env_val
                elif env_key == 'password':
                    self.client['password'] = env_val
                elif env_key == 'password':
                    self.client['password'] = env_val
            else:
                print 'error:', line
        elif line[:15] == '>CLIENT:CONNECT':
            client_id, key_id = line[16:].split(',')
            self.client = {
                'client_id': client_id,
                'key_id': key_id,
            }
        else:
            print 'line:', line

    def wait_for_socket(self):
        for _ in xrange(10000):
            if os.path.exists(self.socket_path):
                return
            time.sleep(0.001)

    def _socket_thread(self):
        data = ''
        while True:
            data += self.sock.recv(1024)
            lines = data.split('\n')
            data = lines.pop()
            for line in lines:
                self.parse_line(line.strip())

    def connect(self):
        self.wait_for_socket()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)

    def start(self):
        thread = threading.Thread(target=self._socket_thread)
        thread.daemon = True
        thread.start()
