from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import utils

import os

def setup_clear_temp():
    for name in os.listdir(settings.conf.temp_path):
        path = os.path.join(settings.conf.temp_path, name)
        #utils.rmtree(path)
