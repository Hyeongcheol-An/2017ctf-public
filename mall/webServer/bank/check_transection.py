#!/usr/bin/python2

'''
Usage:
    $ ./check_transection.py <id> <pw> <expected_money>
    result: success/fail (stdout)
'''

from socket import *
from time import sleep
import sys, re

def recv_until(s, char):
    res = ''
    while True:
        res += s.recv(1)
        if res.endswith(char):
            break
    return res

def send_line(sock, data) :
    data += "\n"
    sock.send(data.encode())

def check_line_by_line(s, keyword):
    while True:
        res = recv_until(s, '\n')
        if keyword in res:
            break
    return res

def login(s, user_id, pwd) :
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "1")
    recv_until(s, " * Username -> ")
    send_line(s, user_id)
    recv_until(s, " * Password -> ")
    send_line(s, pwd)

def logout(s):
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "5")

def terminate(s):
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "3")

def check_balance(s):
    recv_until(s, " What would you like to do? -> ")
    send_line(s, "1")
    result = recv_until(s, " Enter any key to return to the previous menu -> ")
    send_line(s, "Go")
    return result

PORT = 1588

if len(sys.argv) != 5:
    print 'Usage: '
    print '{} <ip> <id> <pw> <expected-money>'.format(sys.argv[0])
    exit(1)

HOST = sys.argv[1]
ID = sys.argv[2]
PW = sys.argv[3]
E_MONEY = int(sys.argv[4])

s = socket(AF_INET, SOCK_STREAM)
s.connect((HOST, PORT))

login(s, ID, PW)
buf = check_balance(s)
balance = int(buf.split("Balance:")[1].split("won")[0].strip())
logout(s)
terminate(s)

s.close()

if balance >= E_MONEY:
    print 'success'
    exit(0)
else:
    print 'fail'
    exit(0)
