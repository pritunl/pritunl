from pritunl import settings

import os
import uuid

def setup_temp_path():
    settings.conf.temp_path = settings.conf.temp_path.replace(
        '%r', uuid.uuid4().hex)
    if not os.path.isdir(settings.conf.temp_path):
        os.makedirs(settings.conf.temp_path)
