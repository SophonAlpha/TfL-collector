#!/bin/bash
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo ----- install InfluxDB -----
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install net-tools
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/os-release
echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt-get install influxdb -y
sudo service influxdb start
sudo aws s3 cp s3://collector-deployment-bucket-m1mgfnap/deployment/influxdb.conf /etc/influxdb/
sudo systemctl restart influxdb
sudo apt-get install influxdb-client -y

echo ----- install Grafana -----
sudo apt-get install -y apt-transport-https
sudo apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo aws s3 cp s3://collector-deployment-bucket-m1mgfnap/deployment/grafana.ini /etc/grafana/

echo ----- install SSL certificates -----
sudo apt-get install ca-certificates -y
sudo aws s3 cp s3://collector-deployment-bucket-m1mgfnap/deployment/sagittarius_eurydika_de.crt /etc/ssl/
sudo aws s3 cp s3://collector-deployment-bucket-m1mgfnap/deployment/sagittarius_eurydika_de.key /etc/ssl/
sudo chown influxdb:influxdb /etc/ssl/sagittarius_eurydika_de.*
sudo chmod 644 /etc/ssl/sagittarius_eurydika_de.crt
sudo chmod 644 /etc/ssl/sagittarius_eurydika_de.key
sudo aws s3 cp s3://collector-deployment-bucket-m1mgfnap/deployment/sagittarius_eurydika_de.ca-bundle.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

echo ----- set permissions to certificates -----
sudo addgroup eurydika_certs
sudo adduser influxdb eurydika_certs
sudo adduser grafana eurydika_certs
sudo chown influxdb:eurydika_certs /etc/ssl/sagittarius_eurydika_de.*
sudo systemctl restart influxdb

echo ----- restore InfluxDB database -----
sudo aws s3 cp s3://collector-deployment-bucket-m1mgfnap/backup_InfluxDB/ /home/ubuntu/backup_InfluxDB/ --recursive
influxd restore -portable /home/ubuntu/backup_InfluxDB/
sudo rm -r /home/ubuntu/backup_InfluxDB/

echo ----- configure InfluxDB users -----
sudo apt-get install jq -y
region=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq --raw-output .region)
cmd='aws ssm get-parameters --region '$region' --names /Collector/InfluxDB_Users --with-decryption --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.collector_InfluxDB_admin_uid'"'"''
admin_uid=$(eval $cmd)
cmd='aws ssm get-parameters --region '$region' --names /Collector/InfluxDB_Users --with-decryption --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.collector_InfluxDB_admin_pw'"'"''
admin_pw=$(eval $cmd)
cmd='aws ssm get-parameters --region '$region' --names /Collector/InfluxDB_Users --with-decryption --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.collector_InfluxDB_grafana_uid'"'"''
grafana_uid=$(eval $cmd)
cmd='aws ssm get-parameters --region '$region' --names /Collector/InfluxDB_Users --with-decryption --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.collector_InfluxDB_grafana_pw'"'"''
grafana_pw=$(eval $cmd)
influx -ssl -host sagittarius.eurydika.de -execute 'CREATE USER '$admin_uid' WITH PASSWORD '"'"$admin_pw"'"' WITH ALL PRIVILEGES'
influx -username $admin_uid -password $admin_pw -ssl -host sagittarius.eurydika.de -execute 'CREATE USER '$grafana_uid' WITH PASSWORD '"'"$grafana_pw"'"''
influx -username $admin_uid -password $admin_pw -ssl -host sagittarius.eurydika.de -execute 'USE TfL'
influx -username $admin_uid -password $admin_pw -ssl -host sagittarius.eurydika.de -execute 'GRANT ALL ON "TfL" TO "grafana"'

echo ----- restore Grafana database -----
sudo systemctl stop grafana-server
sudo aws s3 cp s3://collector-deployment-bucket-m1mgfnap/backup_Grafana/var/lib/ /var/lib/ --recursive
sudo chown -R grafana:grafana /var/lib/grafana
sudo systemctl start grafana-server

echo ----- system restart to apply any updates that require reboot -----
sudo shutdown -r now
