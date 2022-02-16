# pylama:ignore
import requests
import os

os.environ['BOTO_CONFIG'] = ''

try:
    requests.packages.urllib3.disable_warnings()
except:  # FIXME E722 do not use bare 'except' [pep8]
    pass
