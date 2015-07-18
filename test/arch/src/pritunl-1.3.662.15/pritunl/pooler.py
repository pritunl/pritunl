pooler_types = {}

def add_pooler(fill_type):
    def add_pooler_wrap(func):
        pooler_types[fill_type] = func
        return func
    return add_pooler_wrap

def fill(fill_type, *args, **kwargs):
    pooler_types[fill_type](*args, **kwargs)
