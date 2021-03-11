from pritunl import settings
from pritunl import utils
from pritunl import mongo

import os

def set_acme(token, authorization):
    coll = mongo.get_collection('acme_challenges')

    coll.update({
        '_id': token,
    }, {
        '_id': token,
        'authorization': authorization,
        'timestamp': utils.now(),
    }, upsert=True)

def get_authorization(token):
    coll = mongo.get_collection('acme_challenges')

    doc = coll.find_one({
        '_id': token,
    })

    if doc:
        return doc.get('authorization')

def get_acme_cert(account_key, csr):
    from pritunl import acme_tiny

    temp_path = utils.get_temp_path()
    account_key_path = temp_path + '.key'
    csr_path = temp_path + '.csr'

    with open(account_key_path, 'w') as account_key_file:
        os.chmod(account_key_path, 0o600)
        account_key_file.write(account_key)

    with open(csr_path, 'w') as csr_file:
        csr_file.write(csr)

    certificate = acme_tiny.get_crt(
        account_key_path,
        csr_path,
        set_acme,
    )

    cert_path = temp_path + '.crt'
    with open(cert_path, 'w') as cert_file:
        cert_file.write(certificate)

    try:
        os.remove(account_key_path)
    except:
        pass
    try:
        os.remove(csr_path)
    except:
        pass

    return certificate

def update_acme_cert():
    if not settings.app.acme_key:
        settings.app.acme_key = utils.generate_private_key()
        settings.commit()

    private_key = utils.generate_private_ec_key()
    csr = utils.generate_csr(private_key, settings.app.acme_domain)
    cert = get_acme_cert(settings.app.acme_key, csr)

    settings.app.server_key = private_key.strip()
    settings.app.server_cert = cert.strip()
    settings.app.acme_timestamp = utils.time_now()
    settings.commit()
