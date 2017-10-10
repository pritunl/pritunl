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
# host.py
#
# Copyright 2003,2007 Wichert Akkerman <wichert@wiggy.net>

from pritunl.pyrad import packet


class Host:
    """Generic RADIUS capable host.

    :ivar     dict: RADIUS dictionary
    :type     dict: pyrad.dictionary.Dictionary
    :ivar authport: port to listen on for authentication packets
    :type authport: integer
    :ivar acctport: port to listen on for accounting packets
    :type acctport: integer
    """
    def __init__(self, authport=1812, acctport=1813, dict=None):
        """Constructor

        :param authport: port to listen on for authentication packets
        :type  authport: integer
        :param acctport: port to listen on for accounting packets
        :type  acctport: integer
        :param     dict: RADIUS dictionary
        :type      dict: pyrad.dictionary.Dictionary
        """
        self.dict = dict
        self.authport = authport
        self.acctport = acctport

    def CreatePacket(self, **args):
        """Create a new RADIUS packet.
        This utility function creates a new RADIUS authentication
        packet which can be used to communicate with the RADIUS server
        this client talks to. This is initializing the new packet with
        the dictionary and secret used for the client.

        :return: a new empty packet instance
        :rtype:  pyrad.packet.Packet
        """
        return packet.Packet(dict=self.dict, **args)

    def CreateAuthPacket(self, **args):
        """Create a new authentication RADIUS packet.
        This utility function creates a new RADIUS authentication
        packet which can be used to communicate with the RADIUS server
        this client talks to. This is initializing the new packet with
        the dictionary and secret used for the client.

        :return: a new empty packet instance
        :rtype:  pyrad.packet.AuthPacket
        """
        return packet.AuthPacket(dict=self.dict, **args)

    def CreateAcctPacket(self, **args):
        """Create a new accounting RADIUS packet.
        This utility function creates a new accouting RADIUS packet
        which can be used to communicate with the RADIUS server this
        client talks to. This is initializing the new packet with the
        dictionary and secret used for the client.

        :return: a new empty packet instance
        :rtype:  pyrad.packet.AcctPacket
        """
        return packet.AcctPacket(dict=self.dict, **args)

    def SendPacket(self, fd, pkt):
        """Send a packet.

        :param fd: socket to send packet with
        :type  fd: socket class instance
        :param pkt: packet to send
        :type  pkt: Packet class instance
        """
        fd.sendto(pkt.Packet(), pkt.source)

    def SendReplyPacket(self, fd, pkt):
        """Send a packet.

        :param fd: socket to send packet with
        :type  fd: socket class instance
        :param pkt: packet to send
        :type  pkt: Packet class instance
        """
        fd.sendto(pkt.ReplyPacket(), pkt.source)
