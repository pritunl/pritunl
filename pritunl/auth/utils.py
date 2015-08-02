from pritunl import settings

import base64
import hashlib

def hash_password_v0(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:settings.app.password_len_limit])
    pass_hash.update(base64.b64decode(salt))
    return pass_hash.digest()

def hash_password_v1(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:settings.app.password_len_limit])
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for i in xrange(5):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()
    return hash_digest

def hash_password_v2(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:settings.app.password_len_limit])
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for _ in xrange(10):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()
    return hash_digest
