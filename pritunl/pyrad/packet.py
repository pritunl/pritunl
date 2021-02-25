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
# packet.py
#
# Copyright 2002-2005,2007 Wichert Akkerman <wichert@wiggy.net>
#
# A RADIUS packet as defined in RFC 2138


import struct
import random
try:
    import hashlib
    md5_constructor = hashlib.md5
except ImportError:
    # BBB for python 2.4
    import md5
    md5_constructor = md5.new
import six
from pritunl.pyrad import tools

# Packet codes
AccessRequest = 1
AccessAccept = 2
AccessReject = 3
AccountingRequest = 4
AccountingResponse = 5
AccessChallenge = 11
StatusServer = 12
StatusClient = 13
DisconnectRequest = 40
DisconnectACK = 41
DisconnectNAK = 42
CoARequest = 43
CoAACK = 44
CoANAK = 45

# Use cryptographic-safe random generator as provided by the OS.
random_generator = random.SystemRandom()

# Current ID
CurrentID = random_generator.randrange(1, 255)


class PacketError(Exception):
    pass


class Packet(dict):
    """Packet acts like a standard python map to provide simple access
    to the RADIUS attributes. Since RADIUS allows for repeated
    attributes the value will always be a sequence. pyrad makes sure
    to preserve the ordering when encoding and decoding packets.

    There are two ways to use the map intereface: if attribute
    names are used pyrad take care of en-/decoding data. If
    the attribute type number (or a vendor ID/attribute type
    tuple for vendor attributes) is used you work with the
    raw data.

    Normally you will not use this class directly, but one of the
    :obj:`AuthPacket` or :obj:`AcctPacket` classes.
    """

    def __init__(self, code=0, id=None, secret=six.b(''), authenticator=None,
            **attributes):
        """Constructor

        :param dict:   RADIUS dictionary
        :type dict:    pyrad.dictionary.Dictionary class
        :param secret: secret needed to communicate with a RADIUS server
        :type secret:  string
        :param id:     packet identifaction number
        :type id:      integer (8 bits)
        :param code:   packet type code
        :type code:    integer (8bits)
        :param packet: raw packet to decode
        :type packet:  string
        """
        dict.__init__(self)
        self.code = code
        if id is not None:
            self.id = id
        else:
            self.id = CreateID()
        if not isinstance(secret, six.binary_type):
            raise TypeError('secret must be a binary string')
        self.secret = secret
        if authenticator is not None and \
                not isinstance(authenticator, six.binary_type):
                    raise TypeError('authenticator must be a binary string')
        self.authenticator = authenticator

        if 'dict' in attributes:
            self.dict = attributes['dict']

        if 'packet' in attributes:
            self.DecodePacket(attributes['packet'])

        for (key, value) in list(attributes.items()):
            if key in ['dict', 'fd', 'packet']:
                continue
            key = key.replace('_', '-')
            self.AddAttribute(key, value)

    def CreateReply(self, **attributes):
        """Create a new packet as a reply to this one. This method
        makes sure the authenticator and secret are copied over
        to the new instance.
        """
        return Packet(id=self.id, secret=self.secret,
                      authenticator=self.authenticator, dict=self.dict,
                      **attributes)

    def _DecodeValue(self, attr, value):
        if attr.values.HasBackward(value):
            return attr.values.GetBackward(value)
        else:
            return tools.DecodeAttr(attr.type, value)

    def _EncodeValue(self, attr, value):
        if attr.values.HasForward(value):
            return attr.values.GetForward(value)
        else:
            return tools.EncodeAttr(attr.type, value)

    def _EncodeKeyValues(self, key, values):
        if not isinstance(key, str):
            return (key, values)

        attr = self.dict.attributes[key]
        if attr.vendor:
            key = (self.dict.vendors.GetForward(attr.vendor), attr.code)
        else:
            key = attr.code

        return (key, [self._EncodeValue(attr, v) for v in values])

    def _EncodeKey(self, key):
        if not isinstance(key, str):
            return key

        attr = self.dict.attributes[key]
        if attr.vendor:
            return (self.dict.vendors.GetForward(attr.vendor), attr.code)
        else:
            return attr.code

    def _DecodeKey(self, key):
        """Turn a key into a string if possible"""

        if self.dict.attrindex.HasBackward(key):
            return self.dict.attrindex.GetBackward(key)
        return key

    def AddAttribute(self, key, value):
        """Add an attribute to the packet.

        :param key:   attribute name or identification
        :type key:    string, attribute code or (vendor code, attribute code)
                      tuple
        :param value: value
        :type value:  depends on type of attribute
        """
        (key, value) = self._EncodeKeyValues(key, [value])
        value = value[0]

        self.setdefault(key, []).append(value)

    def __getitem__(self, key):
        if not isinstance(key, six.string_types):
            return dict.__getitem__(self, key)

        values = dict.__getitem__(self, self._EncodeKey(key))
        attr = self.dict.attributes[key]
        res = []
        for v in values:
            res.append(self._DecodeValue(attr, v))
        return res

    def __contains__(self, key):
        try:
            return dict.__contains__(self, self._EncodeKey(key))
        except KeyError:
            return False

    has_key = __contains__

    def __delitem__(self, key):
        dict.__delitem__(self, self._EncodeKey(key))

    def __setitem__(self, key, item):
        if isinstance(key, six.string_types):
            (key, item) = self._EncodeKeyValues(key, [item])
            dict.__setitem__(self, key, item)
        else:
            assert isinstance(item, list)
            dict.__setitem__(self, key, item)

    def keys(self):
        return [self._DecodeKey(key) for key in dict.keys(self)]

    @staticmethod
    def CreateAuthenticator():
        """Create a packet autenticator. All RADIUS packets contain a sixteen
        byte authenticator which is used to authenticate replies from the
        RADIUS server and in the password hiding algorithm. This function
        returns a suitable random string that can be used as an authenticator.

        :return: valid packet authenticator
        :rtype: binary string
        """

        data = []
        for i in range(16):
            data.append(random_generator.randrange(0, 256))
        if six.PY3:
            return bytes(data)
        else:
            return ''.join(chr(b) for b in data)

    def CreateID(self):
        """Create a packet ID.  All RADIUS requests have a ID which is used to
        identify a request. This is used to detect retries and replay attacks.
        This function returns a suitable random number that can be used as ID.

        :return: ID number
        :rtype:  integer

        """
        return random_generator.randrange(0, 256)

    def ReplyPacket(self):
        """Create a ready-to-transmit authentication reply packet.
        Returns a RADIUS packet which can be directly transmitted
        to a RADIUS server. This differs with Packet() in how
        the authenticator is calculated.

        :return: raw packet
        :rtype:  string
        """
        assert(self.authenticator)
        assert(self.secret is not None)

        attr = self._PktEncodeAttributes()
        header = struct.pack('!BBH', self.code, self.id, (20 + len(attr)))

        authenticator = md5_constructor(header[0:4] + self.authenticator
                              + attr + self.secret).digest()
        return header + authenticator + attr

    def VerifyReply(self, reply, rawreply=None):
        if reply.id != self.id:
            return False

        if rawreply is None:
            rawreply = reply.ReplyPacket()

        hash = md5_constructor(rawreply[0:4] + self.authenticator +
                     rawreply[20:] + self.secret).digest()

        if hash != rawreply[4:20]:
            return False
        return True

    def _PktEncodeAttribute(self, key, value):
        if isinstance(key, tuple):
            value = struct.pack('!L', key[0]) + \
                self._PktEncodeAttribute(key[1], value)
            key = 26

        return struct.pack('!BB', key, (len(value) + 2)) + value

    def _PktEncodeAttributes(self):
        result = six.b('')
        for (code, datalst) in list(self.items()):
            for data in datalst:
                result += self._PktEncodeAttribute(code, data)

        return result

    def _PktDecodeVendorAttribute(self, data):
        # Check if this packet is long enough to be in the
        # RFC2865 recommended form
        if len(data) < 6:
            return (26, data)

        (vendor, type, length) = struct.unpack('!LBB', data[:6])[0:3]
        # Another sanity check
        if len(data) != length + 4:
            return (26, data)

        return ((vendor, type), data[6:])

    def DecodePacket(self, packet):
        """Initialize the object from raw packet data.  Decode a packet as
        received from the network and decode it.

        :param packet: raw packet
        :type packet:  string"""

        try:
            (self.code, self.id, length, self.authenticator) = \
                    struct.unpack('!BBH16s', packet[0:20])
        except struct.error:
            raise PacketError('Packet header is corrupt')
        if len(packet) != length:
            raise PacketError('Packet has invalid length')
        if length > 8192:
            raise PacketError('Packet length is too long (%d)' % length)

        self.clear()

        packet = packet[20:]
        while packet:
            try:
                (key, attrlen) = struct.unpack('!BB', packet[0:2])
            except struct.error:
                raise PacketError('Attribute header is corrupt')

            if attrlen < 2:
                raise PacketError(
                        'Attribute length is too small (%d)' % attrlen)

            value = packet[2:attrlen]
            if key == 26:
                (key, value) = self._PktDecodeVendorAttribute(value)

            self.setdefault(key, []).append(value)
            packet = packet[attrlen:]


class AuthPacket(Packet):
    def __init__(self, code=AccessRequest, id=None, secret=six.b(''),
            authenticator=None, **attributes):
        """Constructor

        :param code:   packet type code
        :type code:    integer (8bits)
        :param id:     packet identifaction number
        :type id:      integer (8 bits)
        :param secret: secret needed to communicate with a RADIUS server
        :type secret:  string

        :param dict:   RADIUS dictionary
        :type dict:    pyrad.dictionary.Dictionary class

        :param packet: raw packet to decode
        :type packet:  string
        """
        Packet.__init__(self, code, id, secret, authenticator, **attributes)

    def CreateReply(self, **attributes):
        """Create a new packet as a reply to this one. This method
        makes sure the authenticator and secret are copied over
        to the new instance.
        """
        return AuthPacket(AccessAccept, self.id,
            self.secret, self.authenticator, dict=self.dict,
            **attributes)

    def RequestPacket(self):
        """Create a ready-to-transmit authentication request packet.
        Return a RADIUS packet which can be directly transmitted
        to a RADIUS server.

        :return: raw packet
        :rtype:  string
        """
        attr = self._PktEncodeAttributes()

        if self.authenticator is None:
            self.authenticator = self.CreateAuthenticator()

        if self.id is None:
            self.id = self.CreateID()

        header = struct.pack('!BBH16s', self.code, self.id,
            (20 + len(attr)), self.authenticator)

        return header + attr

    def PwDecrypt(self, password):
        """Unobfuscate a RADIUS password. RADIUS hides passwords in packets by
        using an algorithm based on the MD5 hash of the packet authenticator
        and RADIUS secret. This function reverses the obfuscation process.

        :param password: obfuscated form of password
        :type password:  binary string
        :return:         plaintext password
        :rtype:          unicode string
        """
        buf = password
        pw = six.b('')

        last = self.authenticator
        while buf:
            hash = md5_constructor(self.secret + last).digest()
            if six.PY3:
                for i in range(16):
                    pw += bytes((hash[i] ^ buf[i],))
            else:
                for i in range(16):
                    pw += chr(ord(hash[i]) ^ ord(buf[i]))

            (last, buf) = (buf[:16], buf[16:])

        while pw.endswith(six.b('\x00')):
            pw = pw[:-1]

        return pw.decode('utf-8')

    def PwCrypt(self, password):
        """Obfuscate password.
        RADIUS hides passwords in packets by using an algorithm
        based on the MD5 hash of the packet authenticator and RADIUS
        secret. If no authenticator has been set before calling PwCrypt
        one is created automatically. Changing the authenticator after
        setting a password that has been encrypted using this function
        will not work.

        :param password: plaintext password
        :type password:  unicode stringn
        :return:         obfuscated version of the password
        :rtype:          binary string
        """
        if self.authenticator is None:
            self.authenticator = self.CreateAuthenticator()

        if isinstance(password, six.text_type):
            password = password.encode('utf-8')

        buf = password
        if len(password) % 16 != 0:
            buf += six.b('\x00') * (16 - (len(password) % 16))

        hash = md5_constructor(self.secret + self.authenticator).digest()
        result = six.b('')

        last = self.authenticator
        while buf:
            hash = md5_constructor(self.secret + last).digest()
            if six.PY3:
                for i in range(16):
                    result += bytes((hash[i] ^ buf[i],))
            else:
                for i in range(16):
                    result += chr(ord(hash[i]) ^ ord(buf[i]))

            last = result[-16:]
            buf = buf[16:]

        return result


class AcctPacket(Packet):
    """RADIUS accounting packets. This class is a specialization
    of the generic :obj:`Packet` class for accounting packets.
    """

    def __init__(self, code=AccountingRequest, id=None, secret=six.b(''),
            authenticator=None, **attributes):
        """Constructor

        :param dict:   RADIUS dictionary
        :type dict:    pyrad.dictionary.Dictionary class
        :param secret: secret needed to communicate with a RADIUS server
        :type secret:  string
        :param id:     packet identifaction number
        :type id:      integer (8 bits)
        :param code:   packet type code
        :type code:    integer (8bits)
        :param packet: raw packet to decode
        :type packet:  string
        """
        Packet.__init__(self, code, id, secret, authenticator, **attributes)
        if 'packet' in attributes:
            self.raw_packet = attributes['packet']

    def CreateReply(self, **attributes):
        """Create a new packet as a reply to this one. This method
        makes sure the authenticator and secret are copied over
        to the new instance.
        """
        return AcctPacket(AccountingResponse, self.id,
            self.secret, self.authenticator, dict=self.dict,
            **attributes)

    def VerifyAcctRequest(self):
        """Verify request authenticator.

        :return: True if verification failed else False
        :rtype: boolean
        """
        assert(self.raw_packet)
        hash = md5_constructor(self.raw_packet[0:4] + 16 * six.b('\x00') +
                self.raw_packet[20:] + self.secret).digest()
        return hash == self.authenticator

    def RequestPacket(self):
        """Create a ready-to-transmit authentication request packet.
        Return a RADIUS packet which can be directly transmitted
        to a RADIUS server.

        :return: raw packet
        :rtype:  string
        """

        attr = self._PktEncodeAttributes()

        if self.id is None:
            self.id = self.CreateID()

        header = struct.pack('!BBH', self.code, self.id, (20 + len(attr)))
        self.authenticator = md5_constructor(header[0:4] + 16 * six.b('\x00') + attr
            + self.secret).digest()
        return header + self.authenticator + attr


def CreateID():
    """Generate a packet ID.

    :return: packet ID
    :rtype:  8 bit integer
    """
    global CurrentID

    CurrentID = (CurrentID + 1) % 256
    return CurrentID
