class SettingsGroupBase(object):
    group = None
    fields = {}

    def __getattr__(self, name):
        if name in self.fields:
            return self.fields[name]
        raise AttributeError('%s instance has no attribute %r' % (
            self.__class__.__name__, name))
