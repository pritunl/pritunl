from pritunl import settings

import base64
import hashlib
import os

def hash_password_v0(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:settings.app.password_len_limit].encode())
    pass_hash.update(base64.b64decode(salt))
    return pass_hash.digest()

def hash_password_v1(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:settings.app.password_len_limit].encode())
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for i in range(5):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()

    return hash_digest

def hash_password_v2(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:settings.app.password_len_limit].encode())
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for _ in range(10):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()

    return hash_digest

def hash_password_v3(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:settings.app.password_len_limit].encode())
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for _ in range(100000):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()

    return hash_digest

def hash_pin_v1(salt, pin):
    pass_hash = hashlib.sha512()
    pass_hash.update(pin[:settings.app.password_len_limit].encode())
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for _ in range(1024):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()

    return hash_digest

def hash_pin_v2(salt, pin):
    pass_hash = hashlib.sha512()
    pass_hash.update(pin[:settings.app.password_len_limit].encode())
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for _ in range(100000):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()

    return hash_digest

def generate_hash_pin_v2(pin):
    salt = base64.b64encode(os.urandom(8)).decode()
    pin_hash = base64.b64encode(hash_pin_v2(salt, pin)).decode()
    pin_hash = '2$%s$%s' % (salt, pin_hash)

    return pin_hash
