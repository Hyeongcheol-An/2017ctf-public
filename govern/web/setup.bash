#!/bin/bash
set -e

msg () {
    echo -e "\033[1;32m$1\033[0;m"
}

doit () {
    msg "$*"
    $*
}

# Install python packages to virtualenv
doit source env/bin/activate
doit pip install -r requirements.txt

# Write local config
doit cp gov/settings/local.py.template gov/settings/local.py

# Initialize database
doit python manage.py migrate
