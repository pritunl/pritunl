import os

for module_name in os.listdir(os.path.dirname(__file__)):
    if module_name == '__init__.py' or module_name[-3:] != '.py':
        continue
    __import__('pritunl.queues.' + module_name[:-3])
