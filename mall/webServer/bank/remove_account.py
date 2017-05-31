#!/usr/bin/python2

from socket import *
from time import sleep
import sys

def recv_until(sock, until_str) :
    buf = ""
    while True:
        buf += sock.recv(2048).decode()
        if until_str in buf:
            return buf

def send_line(sock, data) :
    data += "\n"
    sock.send(data.encode())

def login(s, user_id, pwd) :
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "1")
    recv_until(s, " * Username -> ")
    send_line(s, user_id)
    recv_until(s, " * Password -> ")
    send_line(s, pwd)

def delete(s, pwd):
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "4")
    recv_until(s, " * Password -> ")
    send_line(s, pwd)
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "2")
    recv_until(s, " Are you ABSOLUTELY sure to remove the account? (Y/N) -> ")
    send_line(s, "Y")
    recv_until(s, " Enter any key to return to the main menu -> ")
    send_line(s, "Go")

def terminate(s):
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "3")

PORT = 1588

if len(sys.argv) != 4:
    exit(1)

HOST = sys.argv[1]
acc = sys.argv[2]
pw = sys.argv[3]

try:
    s = socket(AF_INET, SOCK_STREAM)
    s.connect((HOST, PORT))

    login(s, acc, pw)
    delete(s, pw)
    terminate(s)

    s.close()
except:
    exit(0)
