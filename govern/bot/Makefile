all: setup deps

deps:
	bash install-deps.bash

setup: env
	. env/bin/activate && pip install -r requirement.txt

env:
	virtualenv --python=`which python2.7` env

clean:
	rm -rf env geckodriver.log config.conf

.PHONY: all setup clean
