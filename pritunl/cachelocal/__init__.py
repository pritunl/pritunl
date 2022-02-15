# pylama:ignore=W0401,W0611
from pritunl.cachelocal.cache_trie import *

from pritunl import tunldb

cache_db = tunldb.TunlDB(strict=False)
