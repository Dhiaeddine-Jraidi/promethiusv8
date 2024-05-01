#!/bin/bash

# Stop all processes managed by supervisor
sudo supervisorctl -c /etc/supervisor/supervisord.conf stop all

# Clone the new version into a temporary directory
sudo mkdir -p /tmp/new_version
cd /tmp/new_version
sudo git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git .

# Copy all files except updater.py and update_script.sh to ~/promethiusv8
sudo rsync -av --exclude='update_script.py' --exclude='update_script.sh' ./ ~/promethiusv8

# Clean up temporary directory
cd ~
sudo rm -rf /tmp/new_version
sudo rm -rf ~/promethiusv8/files/download/tracking_opened_trades_logger.txt ~/promethiusv8/files/download/telegram_handler_logger.txt ~/promethiusv8/files/download/main_logger.txt
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all