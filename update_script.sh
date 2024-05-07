#!/bin/bash

RSYNC="/usr/bin/rsync"
SOURCE="/tmp/promethiusv8_new_version/"
DESTINATION="/home/ubuntu/promethiusv8/"

sudo supervisorctl -c /etc/supervisor/supervisord.conf stop all
cd $DESTINATION
sudo rm -rf __pycache__
sudo find . -type f ! \( -name 'main_logger.txt' -o -name 'telegram_handler_logger.txt' -o -name 'tracking_opened_trades_logger.txt' -o -name 'open_trades.csv' -o -name 'syfer_PendingTrades.json' -o -name 'temporary_finished_trade.csv' -o -name 'update_script.sh' \) -exec rm -v {} +
sudo mkdir -p $SOURCE
cd $SOURCE
sudo git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git .
sudo $RSYNC -av --exclude='update_script.sh' $SOURCE $DESTINATION
cd $DESTINATION
sudo pip install -r requirements.txt
sudo cp -f /home/promethiusv8/promethius_runner.conf /etc/supervisor/conf.d/promethius_runner.conf
sudo rm -rf $SOURCE
sudo supervisorctl -c /etc/supervisor/supervisord.conf reread
sudo supervisorctl -c /etc/supervisor/supervisord.conf update
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all