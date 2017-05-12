from pritunl.link.link import Link, Location, Host

from pritunl import settings
from pritunl import mongo

import math

def get_by_id(id):
    return Link(id=id)

def get_host(host_id):
    host = Host(id=host_id)
    if not host:
        return

    host.link = Link(id=host.link_id)
    if not host.link:
        return

    host.location = Location(link=host.link, id=host.location_id)
    if not host.location:
        return

    return host

def iter_links(page=None):
    limit = None
    skip = None
    page_count = settings.app.link_page_count

    if page is not None:
        limit = page_count
        skip = page * page_count if page else 0

    cursor = Link.collection.find({}).sort('name')

    if skip is not None:
        cursor = cursor.skip(page * page_count if page else 0)
    if limit is not None:
        cursor = cursor.limit(limit)

    for doc in cursor:
        yield Link(doc=doc)

def get_page_total():
    collection = mongo.get_collection('servers')

    count = collection.find({}, {
        '_id': True,
    }).count()

    return int(math.floor(max(0, float(count - 1)) /
        settings.app.link_page_count))
