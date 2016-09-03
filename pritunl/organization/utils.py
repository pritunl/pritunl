from pritunl.organization.organization import Organization

from pritunl.constants import *
from pritunl import queue
from pritunl import user
from pritunl import mongo
from pritunl import settings

import threading
import math

def new_pooled():
    thread = threading.Thread(target=new_org, kwargs={
        'type': ORG_POOL,
        'block': False,
    })
    thread.daemon = True
    thread.start()

def reserve_pooled(name=None, auth_api=None, type=ORG_DEFAULT):
    doc = {}

    if name is not None:
        doc['name'] = name
    if auth_api is not None:
        doc['auth_api'] = auth_api
    if type is not None:
        doc['type'] = type

    doc = Organization.collection.find_and_modify({
        'type': ORG_POOL,
    }, {
        '$set': doc,
    }, new=True)

    if doc:
        return Organization(doc=doc)

def new_org(type=ORG_DEFAULT, block=True, **kwargs):
    if type == ORG_DEFAULT:
        org = reserve_pooled(type=type, **kwargs)

        if not org:
            org = queue.reserve('queued_org', block=block, type=type,
                **kwargs)

        if org:
            new_pooled()
            return org

        org = Organization(type=type, **kwargs)
        org.initialize()
        org.commit()

        return org
    else:
        org = Organization(type=type, **kwargs)
        org.queue_initialize(block=block)

        return org

def get_by_id(id, fields=None):
    return Organization(id=id, fields=fields)

def get_by_name(name, fields=None):
    doc = Organization.collection.find_one({
        'name': name,
    }, fields)

    if doc:
        return Organization(doc=doc, fields=fields)

def get_by_token(token, fields=None):
    doc = Organization.collection.find_one({
        'auth_token': token,
    }, fields)

    if doc:
        return Organization(doc=doc, fields=fields)

def iter_orgs(spec=None, type=ORG_DEFAULT, fields=None, page=None):
    limit = None
    skip = None
    page_count = settings.app.org_page_count

    if spec is None:
        spec = {}

    if type is not None:
        spec['type'] = type

    if page is not None:
        limit = page_count
        skip = page * page_count if page else 0

    if fields:
        fields = {key: True for key in fields}

    cursor = Organization.collection.find(spec, fields).sort('name')

    if skip is not None:
        cursor = cursor.skip(page * page_count if page else 0)
    if limit is not None:
        cursor = cursor.limit(limit)

    for doc in cursor:
        yield Organization(doc=doc, fields=fields)

def get_org_page_total():
    org_collection = mongo.get_collection('organizations')

    count = org_collection.find({
        'type': ORG_DEFAULT,
    }, {
        '_id': True,
    }).count()

    return int(math.floor(max(0, float(count - 1)) /
        settings.app.org_page_count))

def get_user_count(org_ids, type=CERT_CLIENT):
    user_collection = mongo.get_collection('users')
    org_user_count = {}

    for org_id in org_ids:
        org_user_count[org_id] = user_collection.find({
            'type': type,
            'org_id': org_id,
        }, {
            '_id': True,
        }).count()

    return org_user_count

def get_user_count_multi(org_ids=None, type=CERT_CLIENT):
    spec = {
        'type': type,
    }
    if org_ids is not None:
        spec['org_id'] = {'$in': org_ids}
    return user.User.collection.find(spec, {
        '_id': True,
    }).count()
