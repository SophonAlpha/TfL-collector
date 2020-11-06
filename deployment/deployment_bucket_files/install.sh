#!/bin/bash

# install InfluxDB
sudo apt install net-tools
sudo apt install awscli -y
sudo apt update
sudo apt upgrade -y
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/os-release
echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt-get update && sudo apt-get install influxdb
sudo service influxdb start
# TODO: copy sagittarius_eurydika_de.key & sagittarius_eurydika_de.crt from S3 to /etc/ssl/
sudo chown influxdb:influxdb /etc/ssl/sagittarius_eurydika_de.*
# TODO: copy influxdb configuration from S3 to /etc/influxdb/influxdb.conf
sudo systemctl restart influxdb




