import os
import re
import subprocess
import sys

import requests

import gnupg


def get_csrf_token(r):
    m = re.search('name=.csrfmiddlewaretoken. value=.([^\'\"]+)', r.content)
    return m.group(1)

def carve_chal(r):
    data = r.content
    pat = '-----BEGIN PGP MESSAGE-----[^\-]+-----END PGP MESSAGE-----'
    m = re.search(pat, data)
    enc_nonce = m.group(0)

    pat = '-----BEGIN PGP PUBLIC KEY BLOCK-----[^\-]+'
    pat += '-----END PGP PUBLIC KEY BLOCK-----'
    m = re.search(pat, data)
    service_pubkey = m.group(0)
    return enc_nonce, service_pubkey

def do_auth(domain, github_id):
    s = requests.Session()

    r = s.get(domain + '/bbs/auth/')
    token = get_csrf_token(r)

    # Get challenge
    r = s.post(domain + '/bbs/auth/chal/',
            {'csrfmiddlewaretoken': token, 'id': github_id})
    enc_nonce, service_pubkey = carve_chal(r)
    token = get_csrf_token(r)

    # Decrypt nonce
    with open('/tmp/nonce.gpg', 'w') as f:
        f.write(enc_nonce)
    os.system('rm -f /tmp/nonce.txt')
    os.system('gpg --decrypt --output /tmp/nonce.txt /tmp/nonce.gpg')
    with open('/tmp/nonce.txt', 'r') as f:
        nonce = f.read()
    nonce = nonce.splitlines()[3].strip()
    print('nonce = {}'.format(nonce))

    # Encrypt nonce
    gpg = gnupg.GPG()
    service_gpg = gpg.import_keys(service_pubkey)
    #service_keyid = gpg.list_keys()[0]['keyid']
    resp = gpg.encrypt(nonce, service_gpg.fingerprints[0], always_trust=True)

    # Login
    r = s.post(domain + '/bbs/auth/resp/',
            {'csrfmiddlewaretoken': token, 'auth_resp': resp})
    token = get_csrf_token(r)

    pw = '1234'
    print('Setting your pw to "{}"'.format(pw))
    s.post(domain + '/bbs/auth/success/',
            {'csrfmiddlewaretoken': token,
             'password': pw,
             'password_check': pw })

    print('sessionid={}'.format(s.cookies['sessionid']))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: {} <site_address> <github_id>".format(sys.argv[0]))
        exit(1)
    domain = sys.argv[1] # "http://localhost:12123"
    github_id = sys.argv[2] # "your_id"
    do_auth(domain, github_id)
