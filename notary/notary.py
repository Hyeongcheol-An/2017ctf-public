import gnupg
import magic
import os
import sys
import socket
import logging
import logging.handlers
import base64
import struct
import random
import string
import traceback
from os.path import expanduser
from threading import Thread
from datetime import datetime
from getpass import getpass

def init_gpg() :
    gnuhome = expanduser("~") + "/.gnupg"
    gpg = gnupg.GPG(gnupghome = gnuhome)
    return gpg

def import_keys(gpg):
    # Import keys of server
    try :
        server_key_data = open('./server.prv').read()
    except :
        print ("Failed to read in server keys")
        exit(0)

    server_key = gpg.import_keys(server_key_data)
    server_key_ID = server_key.fingerprints[0]
    return server_key_ID

def init_server(service_ip):
    # Initiating Server..
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    except (socket.error, e):
        logging.exception("Socket error")
        return -1

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        s.bind((service_ip, 8000))
    except socket.error, e:
        logging.exception("Bind error")
        return -1;

    return s

def get_files(conn, download_path):
    # Get a file from a client and save it as 'temp'
    try:
        logging.info('Receiving File..')
        conn.send("Send file length\n")
        filesize = struct.unpack("<Q", conn.recv(8))[0]

        conn.send("Send file content\n")
        content = conn.recv(filesize)
        recv_file = open(download_path, 'w')
        recv_file.write(content)
        recv_file.close()
        logging.info('File transmission finished')

    except IOError:
        logging.exception("Open error")
        recv_file.close()
        return -1

    except:
        logging.exception("Unexpected error, file transmission failed")
        recv_file.close()
        return -1

    return 1

def verify(conn, gpg, pubkey_dir, passphrase, user_id, download_path):

    for pubkey_filename in os.listdir(pubkey_dir) :
        if pubkey_filename == ("%s.pub" % user_id) :
            # We verify downloaded file
            pubkey_f = open(pubkey_dir + "/" + pubkey_filename)
            pubkey_content = pubkey_f.read()
            pubkey_f.close()
            pubkey = gpg.import_keys(pubkey_content)
            pubkey_owner = pubkey.fingerprints[0]
            input_file = open(download_path, 'rb')
            decrypted = gpg.decrypt_file(input_file, passphrase = passphrase)
            input_file.close()

            if not decrypted.ok or decrypted.fingerprint !=  pubkey_owner:
                # We send a specific string about authentication
                conn.send("XXXXX\n")
                print("Not a valid file")
                return -1
            else:
                conn.send("YYYYY\n")
                decrypted_file = open(download_path, "wb")
                decrypted_file.write(str(decrypted))
                decrypted_file.close()
                return 1 
    return -1


def sign_and_send(conn, gpg, passphrase, server_key_ID, download_path):

    conn.send("Verified, will you receive signature? (Y/N) : ")
    data = conn.recv(8)

    if data.upper().strip() == "Y" :
        dec_file = open(download_path, 'rb')
        signed = gpg.sign_file(dec_file, keyid = server_key_ID, passphrase = passphrase)
        dec_file.close()
        conn.send(signed.data)

def loggingconfig():

    # Initiate Logging handler
    logging.basicConfig(filename='/var/log/notary/test.log',filemode='w',level=logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)

    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logger = logging.getLogger(__name__)
    
    # Initiate FileHandler and Streamhandler
    fileHandler = logging.FileHandler('/var/log/notary/test.log')
    streamHandler = logging.StreamHandler()

# If an error is occured logs it
def errorInConnect(c,comment):
    logging.info('%s', comment)
    c.close()


def handler(conn, passphrase, pubkey_dir):
    try :
        gpg = init_gpg()
        server_key_ID = import_keys(gpg)

        conn.send("Input your ID: ")
        user_id = conn.recv(128).strip()
    
        # SLA checker will connect often, so use fixed filepath to save storage space
        if user_id == "ta" :
            download_path = "./Download/%s" % user_id
        else :
            rand_str = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
            download_path = "./Download/%s_%s" % (user_id, rand_str)

        # 1. Server gets a file from a user
        print ('[Receive file]')
        if get_files(conn, download_path) < 0 :
            errorInConnect(conn,'Get File error')
            return

        print ('[Verification Step]')
        # 2. Server verifies a file given by a user
        if verify(conn, gpg, pubkey_dir, passphrase, user_id, download_path) < 0:
            errorInConnect(conn,'Verify error')
            return

        print ('[Sign & Send]')
        # 3. Server signs the file and return the JSON file to the user
        sign_and_send(conn, gpg, passphrase, server_key_ID, download_path)
        
        conn.close()
        print ('[Terminated]')

    except Exception as e:
        raise e
        conn.close()
        traceback.print_tb(sys.exc_info()[-1])


def main(argv):

    thread_list = []
    # We will run this program with sudo command.
    # Log all events
    loggingconfig()

    # 0. Import public and private keys first

    passphrase = getpass("Input server key passphrase : ")
    pubkey_dir = argv[1]

    # Initiaiting Server
    sock = init_server(argv[2])

    print ('Initiating Server...')
    if sock == -1 :       # get a sock object
        logging.error('Cannot init server')
        sys.exit(1)

    sock.listen(5)
    print ('Server is Listening...')

    while True:
        conn, address = sock.accept()
        logging.info('Connetion established with %s', address)
        print ('Connect from', address)

        thread = Thread(target=handler, args=(conn, passphrase, pubkey_dir))
        thread_list.append(thread)
        thread.start()

        for thread in thread_list:
            if not thread.isAlive():
                thread_list.remove(thread)
                thread.join()

if __name__ == "__main__":
    if len(sys.argv) != 3 :
        print "Provide <pub key dir> and <service ip>"
        sys.exit(1)
    main(sys.argv)
