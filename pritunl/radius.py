#!/usr/bin/env python
'''
Extremly basic RADIUS authentication. Bare minimum required to authenticate
a user, yet remain RFC2138 compliant (I hope).

Homepage at http://github.com/btimby/py-radius/
'''
# Copyright (c) 1999, Stuart Bishop <zen@shangri-la.dropbear.id.au>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the
#     distribution.
#
#     The name of Stuart Bishop may not be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from select import select
from struct import pack,unpack
from random import randint
try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5
import socket

__version__ = '1.0.3'

# Constants
ACCESS_REQUEST	= 1
ACCESS_ACCEPT	= 2
ACCESS_REJECT	= 3

DEFAULT_RETRIES = 3
DEFAULT_TIMEOUT = 5

class Error(Exception): pass
class NoResponse(Error): pass
class SocketError(NoResponse): pass

def authenticate(username,password,secret,host='radius',port=1645):
    '''Return 1 for a successful authentication. Other values indicate
       failure (should only ever be 0 anyway).

       Can raise either NoResponse or SocketError'''

    r = RADIUS(secret,host,port)
    return r.authenticate(username,password)

class RADIUS:

    def __init__(self,secret,host='radius',port=1645):
        self._secret = secret
        self._host   = host
        self._port   = port

        self.retries = DEFAULT_RETRIES
        self.timeout = DEFAULT_TIMEOUT
        self._socket = None

    def __del__(self):
        self.closesocket()

    def opensocket(self):
        if self._socket == None:
            self._socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            self._socket.connect((self._host,self._port))

    def closesocket(self):
        if self._socket is not None:
            try:
                self._socket.close()
            except socket.error as x:
                raise SocketError(x)
            self._socket = None

    def generateAuthenticator(self):
        '''A 16 byte random string'''
        v = list(range(0,17))
        v[0] = '16B'
        for i in range(1,17):
            v[i] = randint(1,255)

        return pack(*v)

    def radcrypt(self,authenticator,text):
        '''Encrypt a password with the secret'''
        # First, pad the password to multiple of 16 octets.
        text += chr(0) * (16 - (len(text) % 16))
        if len(text) > 128:
            raise Exception('Password exceeds maximun of 128 bytes')
        result = ''
        last = authenticator
        while text:
            # md5sum the shared secret with the authenticator,
            # after the first iteration, the authenticator is the previous
            # result of our encryption.
            hash = md5(self._secret + last).digest()
            for i in range(16):
                result += chr(ord(hash[i]) ^ ord(text[i]))
            # The next iteration will act upon the next 16 octets of the password
            # and the result of our xor operation above. We will set last to
            # the last 16 octets of our result (the xor we just completed). And
            # remove the first 16 octets from the password.
            last, text = result[-16:], text[16:]
        return result

    def authenticate(self,uname,passwd):
        '''Attempt t authenticate with the given username and password.
           Returns 0 on failure
           Returns 1 on success
           Raises a NoResponse (or its subclass SocketError) exception if
                no responses or no valid responses are received'''

        try:
            self.opensocket()
            id = randint(0,255)

            authenticator = self.generateAuthenticator()

            encpass = self.radcrypt(authenticator,passwd)

            msg = pack('!B B H 16s B B %ds B B %ds' \
                    % (len(uname),len(encpass)),\
                1,id,
                len(uname)+len(encpass) + 24, # Length of entire message
                authenticator,
                1,len(uname)+2,uname,
                2,len(encpass)+2,encpass)

            for i in range(0,self.retries):
                self._socket.send(msg)

                t = select( [self._socket,],[],[],self.timeout)
                if len(t[0]) > 0:
                    response = self._socket.recv(4096)
                else:
                    continue

                if ord(response[1]) != id:
                    continue

                # Verify the packet is not a cheap forgery or corrupt
                checkauth = response[4:20]
                m = md5(response[0:4] + authenticator + response[20:]
                    + self._secret).digest()

                if m != checkauth:
                    continue

                if ord(response[0]) == ACCESS_ACCEPT:
                    return 1
                else:
                    return 0

        except socket.error as x: # SocketError
            try: self.closesocket()
            except: pass
            raise SocketError(x)

        raise NoResponse

# Don't break code written for radius.py distributed with the ZRadius
# Zope product
Radius = RADIUS

if __name__ == '__main__':

    from getpass import getpass

    host = input("Host? (default = 'radius')")
    port = input('Port? (default = 1645) ')

    if not host: host = 'radius'

    if port: port = int(port)
    else: port = 1645

    secret = ''
    while not secret: secret = getpass('RADIUS Secret? ')

    r = RADIUS(secret,host,port)

    uname,passwd = None,None

    while not uname:  uname = input("Username? ")
    while not passwd: passwd = getpass("Password? ")

    if r.authenticate(uname,passwd):
        print("Authentication Succeeded")
    else:
        print("Authentication Failed")
