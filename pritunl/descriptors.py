class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        obj.__dict__[self.func.__name__] = value = self.func(obj)
        return value

class cached_static_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype):
        if obj is None:
            return self.func(objtype)
        value = self.func(objtype)
        setattr(obj, self.func.__name__, value)
        return value

class static_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype):
        return self.func(objtype)
