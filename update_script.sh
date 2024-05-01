#!/bin/bash

RSYNC="/usr/bin/rsync"
SOURCE="/tmp/new_version/"
DESTINATION="/home/ubuntu/promethiusv8/"

sudo supervisorctl -c /etc/supervisor/supervisord.conf stop all
cd ~/promethiusv8
sudo rm -rf __pycache__
sudo find . -type f ! \( -name 'open_trades.csv' -o -name 'syfer_PendingTrades.json' -o -name 'temporary_finished_trade.csv' -o -name 'update_script.py' -o -name 'update_script.sh' \) -exec rm -v {} +
sudo mkdir -p /tmp/new_version
cd /tmp/new_version
sudo git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git .
sudo $RSYNC -av --exclude='update_script.sh' --exclude='update_script.py' $SOURCE $DESTINATION
sudo rm -rf /tmp/new_version
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all