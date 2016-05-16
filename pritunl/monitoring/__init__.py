from pritunl.monitoring.utils import get_servers

from pritunl import influxdb
from pritunl import utils
from pritunl import settings
from pritunl import logger

import threading

_queue = []
_queue_lock = threading.Lock()
_client = None
_cur_influxdb_uri = None

def insert_point(measurement, tags, fields):
    _queue_lock.acquire()
    try:
        if not _client:
            return

        _queue.append({
            'measurement': settings.app.influxdb_prefix + measurement,
            'tags': tags,
            'time': utils.now(),
            'fields': fields,
        })
    finally:
        _queue_lock.release()

def write_queue():
    global _queue

    _queue_lock.acquire()
    try:
        if not _queue:
            return
        queue = _queue
        _queue = []
        client = _client
    finally:
        _queue_lock.release()

    if client:
        try:
            client.write_points(queue)
        except:
            _queue_lock.acquire()
            try:
                _queue = queue + _queue
            finally:
                _queue_lock.release()
            raise

def connect():
    global _client
    global _cur_influxdb_uri

    influxdb_uri = settings.app.influxdb_uri
    if influxdb_uri == _cur_influxdb_uri:
        return

    if not influxdb_uri:
        _queue_lock.acquire()
        try:
            _client = None
        finally:
            _queue_lock.release()
        _cur_influxdb_uri = influxdb_uri
        return

    hosts, username, password, database = get_servers(influxdb_uri)

    logger.info('Connecting to InfluxDB', 'monitoring',
        influxdb_uri=influxdb_uri,
    )

    if len(hosts) == 1:
        _client = influxdb.InfluxDBClient(
            hosts[0][0],
            hosts[0][1],
            username=username,
            password=password,
            database=database,
        )
    else:
        _client = influxdb.InfluxDBClusterClient(
            hosts,
            username=username,
            password=password,
            database=database,
        )

    _cur_influxdb_uri = influxdb_uri

def init():
    try:
        connect()
    except:
        logger.exception('InfluxDB initial connection error',
            'monitoring',
            influxdb_uri=settings.app.influxdb_uri,
        )
