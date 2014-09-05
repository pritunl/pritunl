from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import pritunl.ipaddress as ipaddress

class VpnIPv4Network(ipaddress.IPv4Network):
    def iterhost_sets(self):
        cur = int(self.network) + 1
        bcast = int(self.broadcast) - 1
        found = False

        for i in xrange(255):
            ip_addr_endpoint = str(ipaddress.IPAddress(
                cur, version=self._version)).split('.')[-1]
            if ip_addr_endpoint in VALID_IP_ENDPOINTS:
                found = True
                break
            cur += 1

        if not found:
            raise TypeError('Invalid IPv4Network')

        while cur <= bcast:
            yield ipaddress.IPAddress(cur, version=self._version), \
                ipaddress.IPAddress(cur + 1, version=self._version)
            cur += 4
