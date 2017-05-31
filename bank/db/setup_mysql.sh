#!/bin/bash
python3 gen_root_pw.py
root_password=$(cat ./root.pw)
export DEBIAN_FRONTEND="noninteractive"
echo PURGE | sudo debconf-communicate mysql-server
echo PURGE | sudo debconf-communicate mysql-server-5.5
echo "mysql-server mysql-server/root_password password ${root_password}" | sudo debconf-set-selections
echo "mysql-server mysql-server/root_password_again password ${root_password}" | sudo debconf-set-selections
sudo apt-get -y install mysql-server
sudo sed -i 's/3306/4406/g' /etc/mysql/my.cnf
sudo /etc/init.d/mysql restart
mysql -uroot -p${root_password} < create_bankdb.sql
sudo pip3 install PyMySQL
./get_pubkey.sh
echo "shoppingmall" >> ./github_id.list
mv /home/bank/shoppingmall.pub ./pubkeys/shoppingmall.pub
python3 reg_pubkey.py
python3 reg_admin.py
echo PURGE | sudo debconf-communicate mysql-server
echo PURGE | sudo debconf-communicate mysql-server-5.5
