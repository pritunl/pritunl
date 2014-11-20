from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings

def setup_app():
    if settings.conf.debug and settings.conf.ssl:
        settings.conf.ssl = False
