from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings

import pymongo
import bson

def setup_app():
    if not pymongo.has_c():
        logger.warning('Failed to load pymongo c bindings')

    if not bson.has_c():
        logger.warning('Failed to load bson c bindings')

    if settings.conf.debug and settings.conf.ssl:
        settings.conf.ssl = False
