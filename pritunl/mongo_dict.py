from pritunl.constants import *
from pritunl.exceptions import *
import UserDict

class MongoDict(UserDict.UserDict, object):
    __class__ = dict

    def __init__(self, initdict=None, changed=True, **kwargs):
        if isinstance(initdict, dict):
            self.data = initdict
        else:
            UserDict.UserDict.__init__(self, initdict, **kwargs)
        self.changed = changed

    def __setitem__(self, *args, **kwargs):
        self.changed = True
        return UserDict.UserDict.__setitem__(self, *args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        self.changed = True
        return UserDict.UserDict.__delitem__(self, *args, **kwargs)

    def clear(self, *args, **kwargs):
        self.changed = True
        return UserDict.UserDict.clear(self, *args, **kwargs)

    def update(self, *args, **kwargs):
        self.changed = True
        return UserDict.UserDict.update(self, *args, **kwargs)

    def setdefault(self, *args, **kwargs):
        self.changed = True
        return UserDict.UserDict.setdefault(self, *args, **kwargs)

    def pop(self, *args, **kwargs):
        self.changed = True
        return UserDict.UserDict.pop(self, *args, **kwargs)

    def popitem(self, *args, **kwargs):
        self.changed = True
        return UserDict.UserDict.popitem(self, *args, **kwargs)
