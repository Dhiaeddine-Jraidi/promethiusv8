#!/bin/bash

RSYNC="/usr/bin/rsync"
SOURCE="/tmp/new_version/"
DESTINATION="/home/ubuntu/promethiusv8/"

sudo supervisorctl -c /etc/supervisor/supervisord.conf stop all
cd $DESTINATION
sudo rm -rf __pycache__
sudo find . -type f ! \( -name 'open_trades.csv' -o -name 'syfer_PendingTrades.json' -o -name 'temporary_finished_trade.csv' -o -name 'update_script.sh' \) -exec rm -v {} +
sudo mkdir -p $SOURCE
cd $SOURCE
sudo git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git .
sudo $RSYNC -av --exclude='update_script.sh' $SOURCE $DESTINATION
sudo rm -rf $SOURCE
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all