#!/usr/bin/python2
import gnupg
from socket import *
from time import sleep
import sys, os
from base64 import b64encode as b64e

'''
Usage:
    $ ./make_account.py

Output(stdout):
    <random_id>
    <random_pw>
'''

def recv_until(sock, until_str) :
    buf = ""
    while True:
        buf += sock.recv(2048).decode()
        if until_str in buf:
            return buf

def send_line(sock, data) :
    data += "\n"
    sock.send(data.encode())

def new_account(i, p):
    # TODO: Since TeamOne's implementation is not completed yet,
    #       this stuff would be postponed

    i = list(i)
    p = list(p)

    for idx in xrange(len(i)):
        if not i[idx].isalnum():
            i[idx] = 'A'

    for idx in xrange(len(p)):
        if not p[idx].isalnum():
            p[idx] = 'A'

    i = 'A' + ''.join(i)
    p = 'A' + ''.join(p)

    return (i, p)

def init_key(pub, pri):
    gpg = gnupg.GPG(gnupghome="/home/mall/.gnupg")
    r = gpg.import_keys(open(pri, "r").read())
    # r = gpg.import_keys(open(pub, "r").read())
    return gpg, r.fingerprints[0]

def remote_exec(s, gpg, server_key_ID, user_id, PW, passphrase):
    ''' ommitted '''
    return

HOST = sys.argv[1]
PORT = 1588
PASSPHRASE = sys.argv[2]

ID_PW_LEN = 9

id_candidate = b64e(os.urandom(ID_PW_LEN))
pw_candidate = b64e(os.urandom(ID_PW_LEN))

s = socket(AF_INET, SOCK_STREAM)
s.connect((HOST, PORT))
gpg, key = init_key("../pub_key.asc", "../priv_key.asc.gpg")
ID, PW = new_account(id_candidate, pw_candidate)
remote_exec(s, gpg, key, ID, PW, PASSPHRASE)

if len(sys.argv) > 3:
    print sys.argv[3], PW
else:
    print ID, PW
