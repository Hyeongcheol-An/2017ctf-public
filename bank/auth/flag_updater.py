#!/usr/bin/env python
import os,sys,socket,random,string,datetime,time
import getpass,gnupg
sys.path.insert(0, '../db')
import utils

SERVERNAME = "IS521-TA <is521-ta@is521-ta.com>"
SERVERKEYID = "AC4B71D8CA031E16"
MYKEYID = "A9DD7F88EE973B0D"
MYPASSPHRASE = "??????????"
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
    print (dec.ok)
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
    print (user)
    print (SERVERNAME)
    return user == SERVERNAME

def isvalid(flag):
    if flag in FLAGSET:
        log("A reused flag detected. Possibly a replay attack?")
        return False
    FLAGSET.add(flag)
    return True

def update(flag):

    bank_db = utils.bankDB()
    try:
        bank_db.set_flag(flag)
        return True
    except:
        return False
    

def handle(conn, gpg):
    r = recv_timeout(conn)
    flag, user = decrypt(gpg, r)
    if flag and verified(user) and isvalid(flag):
        if (update(flag)) :
            log("Flag updated.")
            conn.send(encrypt(gpg, flag).encode())
        else:
            log("Error : can update flag in DB")
    else:
        log("Untrusted request.")

def main(argv):
    global MYPASSPHRASE

    if len(argv) != 3:
        print ("Provide IP and port")
        sys.exit(1)

    random.seed(datetime.datetime.now())
    #MYPASSPHRASE = getpass.getpass("Enter passphrase: ")
    #mysql_pw = getpass.getpass("Enter MySQL password: ")
    passphrase_file = open("/root/passphrase.txt", "rt")
    MYPASSPHRASE = passphrase_file.read().strip()
    passphrase_file.close()
    
    mysql_pw_file = open("/root/mysql_pw.txt", "rt")
    mysql_pw = mysql_pw_file.read().strip()
    mysql_pw_file.close()
    utils.mysql_pw = mysql_pw

    gpg = gnupg.GPG(gnupghome="/root/.gnupg/")
    gpg.import_keys(open("/root/flag.prv").read())
    gpg.import_keys(open("/root/ta.pub").read())

    s = netinit(argv[1], int(argv[2]))
    while True:
        conn, addr = s.accept()
        log("Connection from " + addr[0] + ':' + str(addr[1]))
        handle(conn, gpg)
        conn.close()
    s.close()

if __name__ == "__main__":
    main(sys.argv)
