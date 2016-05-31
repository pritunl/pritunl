import inspect

def get_functions(module):
    funcs = {}
    for x in inspect.getmembers(module):
        if inspect.isfunction(x[1]):
            funcs[x[0]] = x[1]
    return funcs
