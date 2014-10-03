from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings

import os

def setup_temp_path():
    # TODO
    settings.conf.temp_path = 'tmp/pritunl'
    if not os.path.isdir(settings.conf.temp_path):
        os.makedirs(settings.conf.temp_path)
