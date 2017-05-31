all: setup

setup: env
	bash setup.bash

env:
	virtualenv --python=`which python3` env

clean:
	rm -rf env gov/db.sqlite3

.PHONY: all setup clean
