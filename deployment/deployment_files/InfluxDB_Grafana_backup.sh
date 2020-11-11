#!/bin/bash

# backup InfluxDB
influxd backup -portable /home/ubuntu/backup_temp/
rm /home/ubuntu/share/InfluxDB_backup.zip
zip -r -m /home/ubuntu/share/InfluxDB_backup.zip /home/ubuntu/backup_temp/*

# backup Grafana 
sudo zip -r /home/ubuntu/share/Grafana_backup.zip /var/lib/grafana/*
sudo zip -r /home/ubuntu/share/Grafana_backup.zip /var/log/grafana/*
sudo zip -r /home/ubuntu/share/Grafana_backup.zip /etc/grafana/*
