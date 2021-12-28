from pritunl.constants import *
from pritunl import logger

import bson
import time

start = time.time()

def ObjectId(oid=None):
    if oid is not None:
        oid = str(oid)
    if oid is None or len(oid) != 32:
        try:
            return bson.ObjectId(oid)
        except:
            logger.exception('Failed to convert object id', 'utils',
                object_id=oid,
            )
    return oid

def ObjectIdSilent(oid=None):
    if oid is not None:
        oid = str(oid)
    if oid is None or len(oid) != 32:
        return bson.ObjectId(oid)
    return oid

def ParseObjectId(oid):
    if oid:
        return bson.ObjectId(str(oid))
