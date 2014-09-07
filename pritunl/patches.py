from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.mongo_dict import MongoDict
from pritunl.mongo_list import MongoList
import json

class JSONEncoderPatched(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (MongoDict, MongoList)):
            return obj.data
        raise TypeError(repr(obj) + ' is not JSON serializable')
dumps_orig = json.dumps
def dumps_patched(*args, **kwargs):
    if not kwargs.get('cls'):
        kwargs['cls'] = JSONEncoderPatched
    return dumps_orig(*args, **kwargs)
json.dumps = dumps_patched
