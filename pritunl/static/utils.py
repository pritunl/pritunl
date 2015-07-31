import sys
import zlib
import time

def generate_etag(file_name, file_size, mtime):
    file_name = file_name.encode(sys.getfilesystemencoding())
    return 'wzsdm-%d-%s-%s' % (
        time.mktime(mtime.timetuple()),
        file_size,
        zlib.adler32(file_name) & 0xffffffff,
    )
