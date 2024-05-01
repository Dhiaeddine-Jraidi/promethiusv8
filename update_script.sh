#!/bin/bash

# Stop all processes managed by supervisor
sudo supervisorctl -c /etc/supervisor/supervisord.conf stop all

# Navigate to the directory containing the current version
cd ~/promethiusv8

# Clone the new version into a temporary directory
sudo mkdir -p /tmp/new_version
cd /tmp/new_version
git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git .

# Copy all files except updater.py and update_script.sh to ~/promethiusv8
rsync -av --exclude='updater.py' --exclude='update_script.sh' ./ ~/promethiusv8

# Clean up temporary directory
cd ~
sudo rm -rf /tmp/new_version
sudo supervisorctl -c /etc/supervisor/supervisord.conf start all
