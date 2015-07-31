from pritunl import logger

import pymongo
import bson

def setup_check():
    if not pymongo.has_c():
        logger.warning('Failed to load pymongo c bindings')

    if not bson.has_c():
        logger.warning('Failed to load bson c bindings')
