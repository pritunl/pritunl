from pritunl.setup.mongo import setup_mongo
from pritunl.setup.poolers import setup_poolers
from pritunl.setup.public_ip import setup_public_ip

def setup_all():
    setup_mongo()
    setup_poolers()
    setup_public_ip()
