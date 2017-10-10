import requests
import os

os.environ['BOTO_CONFIG'] = ''

try:
    requests.packages.urllib3.disable_warnings()
except:
    pass
