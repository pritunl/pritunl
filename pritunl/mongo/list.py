import collections
import abc

class ListMeta(abc.ABCMeta):
    def __instancecheck__(cls, other):
        if isinstance(other, list):
            return True
        return False

class MongoList(collections.UserList):
    __class__ = list

    def __init__(self, initlist=None, changed=True, **kwargs):
        if isinstance(initlist, list):
            self.data = initlist
        else:
            collections.UserList.__init__(self, initlist, **kwargs)
        self.changed = changed

    def __setitem__(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.__setitem__(self, *args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.__delitem__(self, *args, **kwargs)

    def __setslice__(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.__setslice__(self, *args, **kwargs)

    def __delslice__(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.__delslice__(self, *args, **kwargs)

    def __iadd__(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.__iadd__(self, *args, **kwargs)

    def __imul__(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.__imul__(self, *args, **kwargs)

    def append(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.append(self, *args, **kwargs)

    def insert(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.insert(self, *args, **kwargs)

    def pop(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.pop(self, *args, **kwargs)

    def remove(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.remove(self, *args, **kwargs)

    def reverse(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.reverse(self, *args, **kwargs)

    def sort(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.sort(self, *args, **kwargs)

    def extend(self, *args, **kwargs):
        self.changed = True
        return collections.UserList.extend(self, *args, **kwargs)
