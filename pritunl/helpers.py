import time
import signal

_interrupt = False
_app_server_interrupt = False

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
        try:
            for _ in call(*args, **kwargs):
                if _interrupt:
                    return
        except GeneratorExit:
            pass
    return _wrapped

def interrupter_generator(call):
    def _wrapped(*args, **kwargs):
        for value in call(*args, **kwargs):
            if _interrupt:
                return
            if value is not None:
                yield value
    return _wrapped

def interrupter_sleep(length):
    if _interrupt:
        return
    while True:
        sleep = min(0.5, length)
        time.sleep(sleep)
        length -= sleep
        if _interrupt or length <= 0:
            return

def check_global_interrupt():
    return _interrupt

def set_global_interrupt():
    global _interrupt
    if _interrupt:
        return
    _interrupt = True

    from pritunl import logger
    logger.info('Stopping server', 'setup')
    signal.alarm(3)

def check_app_server_interrupt():
    return _app_server_interrupt

def set_app_server_interrupt():
    global _app_server_interrupt
    _app_server_interrupt = True

def clear_app_server_interrupt():
    global _app_server_interrupt
    _app_server_interrupt = False
