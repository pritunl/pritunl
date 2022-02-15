# pylama:ignore=E302
_nonces = set()

def nonces_add(nonce):
    _nonces.add(nonce)

def nonces_contains(nonce):
    return nonce in _nonces
