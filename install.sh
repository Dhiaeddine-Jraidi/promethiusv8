#!/bin/bash

DOWNLOAD_DIRECTORY="/home/ubuntu/promethiusv8/files/download/"
LOGGER_DIRECTORY="/home/ubuntu/promethiusv8/files/logger/"

sudo apt update
sudo apt upgrade
sudo apt install -y python3 python3-pip git supervisor
sudo service supervisor start
git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git
sudo chmod a+rwx promethiusv8
sudo chmod +x /home/ubuntu/promethiusv8/files/soft_update_script.sh
sudo chmod +x /home/ubuntu/promethiusv8/files/hard_update_script.sh


cd promethiusv8
sudo pip install -r requirements.txt

if [ ! -d "$DOWNLOAD_DIRECTORY" ]; then
    sudo mkdir -p "$DOWNLOAD_DIRECTORY"

fi 

if [ ! -d "$LOGGER_DIRECTORY" ]; then
    sudo mkdir -p "$LOGGER_DIRECTORY"
fi


sudo cp -f /home/ubuntu/promethiusv8/promethius_runner.conf /etc/supervisor/conf.d/promethius_runner.conf
sudo supervisorctl -c /etc/supervisor/supervisord.conf reread
sudo supervisorctl -c /etc/supervisor/supervisord.conf update
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all