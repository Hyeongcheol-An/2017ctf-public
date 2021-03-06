#!/bin/bash
set -x
pw=$(cat ../rootpw)
echo "mysql-server mysql-server/root_password password ${pw}" | sudo debconf-set-selections
echo "mysql-server mysql-server/root_password_again password ${pw}" | sudo debconf-set-selections
sudo apt-get -y install mysql-server
mysql -uroot -p${pw} < resetTable.sql
mysql -uroot -p${pw} < insertData.sql
