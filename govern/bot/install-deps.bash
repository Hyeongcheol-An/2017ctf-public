#!/bin/bash
set -e

msg () {
    echo -e "\033[1;32m$1\033[0;m"
}

doit () {
    msg "$*"
    $*
}

doit sudo apt-get install -y firefox-esr xvfb

if [ ! -f /usr/local/bin/geckodriver ]; then
    doit curl -Lo /tmp/gecko.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.14.0/geckodriver-v0.14.0-linux32.tar.gz
    doit cd /tmp && tar xf /tmp/gecko.tar.gz
    doit sudo mv /tmp/geckodriver /usr/local/bin/geckodriver
fi
