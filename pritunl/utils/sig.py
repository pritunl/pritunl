import base64
import hashlib
import hmac

def get_sig(sig_str, secret):
    return base64.b64encode(
        hmac.new(secret, sig_str, hashlib.sha512).digest(),
    )
