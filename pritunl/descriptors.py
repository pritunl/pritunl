class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        obj.__dict__[self.func.__name__] = value = self.func(obj)
        return value
