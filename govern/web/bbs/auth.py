import json
import os
import random
import re

import gnupg
from django.conf import settings


def _sanitize_id(auth_id):
    return re.match(r'^[a-zA-Z0-9\-_]+$', auth_id) is not None

def generate_challenge(auth_id):
    '''
    Given auth_id, generates a random nonce and
    the nonce value signed with the private key of server
    and encrypted with the public key of auth_id.
    Returns a 2-tuple (nonce as string, encrypted_nonce as string).
    Returns None on error.
    '''
    # Block directory traversal attack.
    if not _sanitize_id(auth_id):
        return None

    '''
    # Generate nonce
    nonce = str(random.randint(0, 2**64))

    # Load service private key
    gpg = gnupg.GPG()
    print(gpg.list_keys())
    key_path = settings.SERVICE_PRIVKEY
    service_key = None
    with open(key_path, 'r') as f:
        service_key = gpg.import_keys(f.read())

    # Sign nonce with server private key
    signed_nonce = gpg.sign(nonce)

    # Load student's public key
    gpg = gnupg.GPG()
    key_name = '{}.pub'.format(auth_id)
    key_path = os.path.join(settings.STUDENT_PUBKEY_DIR, key_name)
    user_key = None
    try:
        with open(key_path, "r") as f:
            user_key = gpg.import_keys(f.read())
    except FileNotFoundError:
        return None

    # Encrypt signed_nonce with user's public key
    enc_nonce = gpg.encrypt(str(signed_nonce),
                            user_key.fingerprints[0],
                            always_trust=True)
    '''

    nonce = str(random.randint(0, 2**64))

    gpg = gnupg.GPG()

    key_name = '{}.pub'.format(auth_id)
    key_path = os.path.join(settings.STUDENT_PUBKEY_DIR, key_name)
    user_key = None
    try:
        with open(key_path, 'r') as f:
            c = f.read()
            user_key = gpg.import_keys(c)
    except FileNotFoundError:
        return None

    key_path = settings.SERVICE_PRIVKEY
    service_key = None
    with open(key_path, 'r') as f:
        c = f.read()
        service_key = gpg.import_keys(c)

    passphrase = settings.SERVICE_PRIVKEY_PASSPHRASE

    enc_nonce = gpg.encrypt(nonce, user_key.fingerprints[0],
                            sign = service_key.fingerprints[0],
                            passphrase = passphrase,
                            always_trust = True)

    return (nonce, enc_nonce)

def get_service_pubkey():
    key_path = settings.SERVICE_PUBKEY
    with open(key_path, 'r') as f:
        pubkey = f.read()
    return pubkey

def verify_response(auth_nonce, auth_resp):
    '''
    Given auth_nonce and auth_resp, decrypts the auth_resp
    and check if the content is equal to auth_nonce.
    '''
    # Load service private key
    gpg = gnupg.GPG()
    key_path = settings.SERVICE_PRIVKEY
    passphrase = settings.SERVICE_PRIVKEY_PASSPHRASE
    with open(key_path, 'r') as f:
        gpg.import_keys(f.read())
    pt = gpg.decrypt(auth_resp, passphrase=passphrase)
    resp_nonce = pt.data.decode('utf-8').strip()
    return resp_nonce == auth_nonce

def verify_notary(auth_id, proof):
    '''
    Given PGP-signed document proof, check if it is
    signed by the notary and the content is legit.
    '''
    # Load notary public key
    gpg = gnupg.GPG()
    key_path = settings.NOTARY_PUBKEY
    with open(key_path, 'r') as f:
        notary_key = gpg.import_keys(f.read())

    # Unpack the payload
    payload = gpg.decrypt(proof)
    try:
        document = json.loads(payload.data.decode('utf-8'))
        proof_id = document['id']
        proof_pubkey = gpg.import_keys(document['pubkey'])
    except ValueError:
        return False
    except KeyError:
        return False

    # Compare the requested person and the id in the payload.
    if auth_id != proof_id:
        return False

    # Load the known public key
    key_name = '{}.pub'.format(proof_id)
    key_path = os.path.join(settings.STUDENT_PUBKEY_DIR, key_name)
    try:
        with open(key_path, "r") as f:
            known_pubkey = gpg.import_keys(f.read())
    except FileNotFoundError:
        return False

    # Check the public key
    if proof_pubkey.fingerprints[0] != known_pubkey.fingerprints[0]:
        return False

    # Check the signature
    verify = gpg.verify(proof)
    if not verify:
        return False
    if verify.pubkey_fingerprint != notary_key.fingerprints[0]:
        return False
    return True
