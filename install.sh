#!/bin/bash

sudo apt update
sudo apt upgrade
sudo apt install -y unzip wget nano python3 python3-pip git
git clone https://github.com/Dhiaeddine-Jraidi/promethiusv8.git
sudo chmod a+rwx promethiusv8
cd promethiusv8
sudo pip install -r requirements.txt
sudo cp supervisord.conf /etc/supervisord.conf
sudo supervisord -c /etc/supervisord.conf