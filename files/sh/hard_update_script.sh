#!/bin/bash

RSYNC="/usr/bin/rsync"
SOURCE="/tmp/promethiusv8_new_version/"
DESTINATION="/home/ubuntu/promethiusv8/"
DOWNLOAD_DIRECTORY="/home/ubuntu/promethiusv8/files/download/"
LOGGER_DIRECTORY="/home/ubuntu/promethiusv8/files/logger/"


sudo supervisorctl -c /etc/supervisor/supervisord.conf stop all
cd $DESTINATION
sudo rm -rf __pycache__
sudo find . -type f ! \( -name 'hard_update_script.sh' \) -exec rm -v {} +
sudo mkdir -p $SOURCE
cd $SOURCE
sudo git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git .

sudo $RSYNC -av --exclude='hard_update_script.sh' $SOURCE $DESTINATION

cd $DESTINATION

if [ ! -d "$DOWNLOAD_DIRECTORY" ]; then
    sudo mkdir -p "$DOWNLOAD_DIRECTORY"

fi 

if [ ! -d "$LOGGER_DIRECTORY" ]; then
    sudo mkdir -p "$LOGGER_DIRECTORY"
fi

sudo pip install -r requirements.txt
sudo cp -f /home/ubuntu/promethiusv8/promethius_runner.conf /etc/supervisor/conf.d/promethius_runner.conf
sudo rm -rf $SOURCE
sudo supervisorctl -c /etc/supervisor/supervisord.conf reread
sudo supervisorctl -c /etc/supervisor/supervisord.conf update
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all