#!/bin/bash
sudo apt update
sudo apt upgrade
sudo apt install -y python3 python3-pip git supervisor
sudo service supervisor start
git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git
sudo chmod a+rwx promethiusv8
cd promethiusv8
sudo chmod +x update_script.sh
sudo pip install -r requirements.txt
sudo cp -f ~/promethiusv8/promethius_runner.conf /etc/supervisor/conf.d/promethius_runner.conf
sudo supervisorctl -c /etc/supervisor/supervisord.conf reread
sudo supervisorctl -c /etc/supervisor/supervisord.conf update
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all