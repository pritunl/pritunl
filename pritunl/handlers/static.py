from pritunl.constants import *
from pritunl.static_file import StaticFile
from pritunl import app_server
import os

@app_server.app.route('/', methods=['GET'])
def index_get():
    file_path = os.path.join(app_server.www_path, 'index.html')
    static_file = StaticFile(file_path, cache=False)
    return static_file.get_response()

@app_server.app.route('/s/<path:file_path>', methods=['GET'])
def static_get(file_path):
    file_path = os.path.join(app_server.www_path, file_path)
    static_file = StaticFile(file_path)
    return static_file.get_response()
