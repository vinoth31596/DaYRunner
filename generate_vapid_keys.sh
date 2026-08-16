#!/bin/bash
set -e
openssl ecparam -name prime256v1 -genkey -noout -out private_key.pem
openssl ec -in private_key.pem -pubout -out public_key.pem
python3 - <<'PY'
from cryptography.hazmat.primitives import serialization
import base64
p=serialization.load_pem_private_key(open('private_key.pem','rb').read(),password=None)
raw=p.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)
print('VAPID_PUBLIC_KEY='+base64.urlsafe_b64encode(raw).rstrip(b'=').decode())
print('VAPID_PRIVATE_KEY='+__import__('os').path.abspath('private_key.pem'))
PY
