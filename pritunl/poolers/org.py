from pritunl.constants import *
from pritunl import settings
from pritunl import pooler
from pritunl import mongo
from pritunl import organization

@pooler.add_pooler('org')
def fill_org():
    collection = mongo.get_collection('organizations')
    queue_collection = mongo.get_collection('queue')

    org_pool_count = collection.count_documents({
        'type': ORG_POOL,
    })

    org_pool_count += queue_collection.count_documents({
        'type': 'init_org_pooled',
    })

    for _ in range(settings.app.org_pool_size - org_pool_count):
        org = organization.new_org(type=ORG_POOL, block=False)
