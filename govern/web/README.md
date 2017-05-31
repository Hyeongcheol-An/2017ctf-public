# TeamFive/web

Government web service.

Written in Python 3 and Django 1.11.


## Requirements

- Python 3
- Virtualenv (recommended)
- gpg


## Config

    cd gov/settings/
    cp local.py.template local.py

And then put following variables:

- `SECRET_KEY`: Long random string.
- `STUDENT_PUBKEY_DIR`: Absolute path to the directory that contains all students public keys.
- `NOTARY_PUBKEY`: Absolute path to the public key of notary service.
- `SERVICE_PUBKEY`: Absolute path to the public key of this service.
- `SERVICE_PRIVKEY`: Absolute path to the private key of this service.
- `SERVICE_PRIVKEY_PASSPHRASE`: Passphrase for the private key of this service.

If you want to run in debug mode, replace `from .prod import *` by `from .dev import *`.

Later, this part will be automated with `Makefile`.


## Setup

    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser


## Run

    python manage.py runserver 0:12345

