from pritunl.host.host import Host
from pritunl.host.usage import HostUsage
from pritunl.host.utils import *

from pritunl import docdb

global_clients = docdb.DocDb(
    'instance_id',
    'client_id',
)
