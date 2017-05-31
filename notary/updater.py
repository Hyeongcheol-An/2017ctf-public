#!/usr/bin/env python
import os,sys,socket,random,string,datetime,time
import getpass,gnupg

SERVERNAME = "IS521-TA <is521-ta@is521-ta.com>"
SERVERKEYID = "AC4B71D8CA031E16"
MYKEYID = "A9DD7F88EE973B0D"
MYPASSPHRASE = "??????????"
FLAGDIR = "/var/ctf/"
FLAGSET = set({})

def recv_timeout(s, timeout=2):
    s.setblocking(0)
    total_data = [];
    data = '';
    begin = time.time()

    while 1:
        if total_data and time.time()-begin > timeout:
            break
        elif time.time()-begin > timeout*2:
            break

        try:
            data = s.recv(8192).decode()
            if data:
                total_data.append(data)
                begin = time.time()
            else:
                time.sleep(0.1)
        except:
            pass

    return ''.join(total_data)

def log(msg):
    print("[" + str(datetime.datetime.now()) + "] " + msg)

def dirinit(path):
    if not os.path.isdir(path):
        os.makedirs(path) # XXX recursive?
    flag = os.path.join(path, "notary.flag")
    with open(flag, "w"):
        os.utime(flag, None)
    os.chmod(flag, 0o604)
    return flag

def netinit(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((ip, port))
    except socket.error as msg:
        log("Bind failed: " + str(msg[0]))
        sys.exit(1)

    s.listen(10)
    return s

def decrypt(gpg, data):
    dec = gpg.decrypt(data, passphrase=MYPASSPHRASE)
    user = dec.username
    if dec.ok and user:
        return str(dec), user
    return False, False

def encrypt(gpg, data):
    e = gpg.encrypt(data,
                    SERVERKEYID,
                    always_trust=True,
                    sign=MYKEYID,
                    passphrase=MYPASSPHRASE)
    return str(e)

def verified(user):
    return user == SERVERNAME

def isvalid(flag):
    if flag in FLAGSET:
        log("A reused flag detected. Possibly a replay attack?")
        return False
    FLAGSET.add(flag)
    return True

def update(path, flag):
    with open(path, "w") as f:
        f.write(flag)
    log("Flag updated.")
    return True

def handle(conn, gpg, flagpath):
    r = recv_timeout(conn)
    flag, user = decrypt(gpg, r)
    if flag and verified(user) and isvalid(flag):
        update(flagpath, flag)
        conn.send(encrypt(gpg, flag).encode())
    else:
        log("Untrusted request.")

def main(argv):
    global MYPASSPHRASE

    if len(argv) != 3:
        sys.exit(1)

    random.seed(datetime.datetime.now())
    with open('/root/passphrase.txt') as f:
        MYPASSPHRASE = f.read().strip()
    gpg = gnupg.GPG(gnupghome = "/root/.gnupg/")
    gpg.import_keys(open('/root/ta.pub').read())
    gpg.import_keys(open('/root/flag.prv').read())
    flagpath = dirinit(FLAGDIR)
    s = netinit(argv[1], int(argv[2]))
    while True:
        conn, addr = s.accept()
        log("Connection from " + addr[0] + ':' + str(addr[1]))
        handle(conn, gpg, flagpath)
        conn.close()
    s.close()

if __name__ == "__main__":
    main(sys.argv)
