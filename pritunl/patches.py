import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning, module='iptc')

import requests
import os

os.environ['BOTO_CONFIG'] = ''

try:
    requests.packages.urllib3.disable_warnings()
except:
    pass
