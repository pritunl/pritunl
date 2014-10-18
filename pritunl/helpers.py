_interrupt = False

class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.func.__name__, value)
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

def interrupter(call):
    def _wrapped(*args, **kwargs):
        for _ in call(*args, **kwargs):
            if _interrupt:
                return
    return _wrapped

def interrupter_generator(call):
    def _wrapped(*args, **kwargs):
        for value in call(*args, **kwargs):
            if _interrupt:
                return
            if value is not None:
                yield value
    return _wrapped

def set_global_interrupt():
    global _interrupt
    _interrupt = True
