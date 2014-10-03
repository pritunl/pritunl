from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings

def setup_app():
    if settings.conf.debug and settings.conf.ssl:
        settings.conf.ssl = False
