# Copyright 2002-2008 Wichert Akkerman. All rights reserved.
# Copyright 2007-2008 Simplon. All rights reserved.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
# curved.py
#
# Copyright 2002 Wichert Akkerman <wichert@wiggy.net>

"""Twisted integration code
"""

__docformat__ = 'epytext en'

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import log
import sys
from pritunl.pyrad import dictionary
from pritunl.pyrad import host
from pritunl.pyrad import packet


class PacketError(Exception):
    """Exception class for bogus packets

    PacketError exceptions are only used inside the Server class to
    abort processing of a packet.
    """


class RADIUS(host.Host, protocol.DatagramProtocol):
    def __init__(self, hosts={}, dict=dictionary.Dictionary()):
        host.Host.__init__(self, dict=dict)
        self.hosts = hosts

    def processPacket(self, pkt):
        pass

    def createPacket(self, **kwargs):
        raise NotImplementedError('Attempted to use a pure base class')

    def datagramReceived(self, datagram, xxx_todo_changeme):
        (host, port) = xxx_todo_changeme
        try:
            pkt = self.CreatePacket(packet=datagram)
        except packet.PacketError as err:
            log.msg('Dropping invalid packet: ' + str(err))
            return

        if host not in self.hosts:
            log.msg('Dropping packet from unknown host ' + host)
            return

        pkt.source = (host, port)
        try:
            self.processPacket(pkt)
        except PacketError as err:
            log.msg('Dropping packet from %s: %s' % (host, str(err)))


class RADIUSAccess(RADIUS):
    def createPacket(self, **kwargs):
        self.CreateAuthPacket(**kwargs)

    def processPacket(self, pkt):
        if pkt.code != packet.AccessRequest:
            raise PacketError(
                    'non-AccessRequest packet on authentication socket')


class RADIUSAccounting(RADIUS):
    def createPacket(self, **kwargs):
        self.CreateAcctPacket(**kwargs)

    def processPacket(self, pkt):
        if pkt.code != packet.AccountingRequest:
            raise PacketError(
                    'non-AccountingRequest packet on authentication socket')


if __name__ == '__main__':
    log.startLogging(sys.stdout, 0)
    reactor.listenUDP(1812, RADIUSAccess())
    reactor.listenUDP(1813, RADIUSAccounting())
    reactor.run()
