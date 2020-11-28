#!/bin/bash
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo -----
echo ----- get deployment folder name -----
echo -----
sudo apt-get update
sudo apt-get install jq -y
region=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq --raw-output .region)
cmd='aws ssm get-parameters --region '$region' --names /Collector/deployment/S3bucket --query '"'"'Parameters[0].Value'"'"' --output text'
deployment_bucket=$(eval $cmd)

echo -----
echo ----- install InfluxDB -----
echo -----
sudo apt-get upgrade -y
sudo apt-get install net-tools
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/os-release
echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt-get install influxdb -y
sudo service influxdb start
sudo aws s3 cp s3://$deployment_bucket/deployment/influxdb.conf /etc/influxdb/
sudo systemctl restart influxdb
sudo apt-get install influxdb-client -y

echo -----
echo ----- install Grafana -----
echo -----
sudo apt-get install -y apt-transport-https
sudo apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo aws s3 cp s3://$deployment_bucket/deployment/grafana.ini /etc/grafana/

echo -----
echo ----- install SSL certificates -----
echo -----
sudo apt-get install ca-certificates -y
sudo aws s3 cp s3://$deployment_bucket/deployment/sagittarius_eurydika_de.crt /etc/ssl/
sudo aws s3 cp s3://$deployment_bucket/deployment/sagittarius_eurydika_de.key /etc/ssl/
sudo chown influxdb:influxdb /etc/ssl/sagittarius_eurydika_de.*
sudo chmod 644 /etc/ssl/sagittarius_eurydika_de.crt
sudo chmod 644 /etc/ssl/sagittarius_eurydika_de.key
sudo aws s3 cp s3://$deployment_bucket/deployment/sagittarius_eurydika_de.ca-bundle.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

echo -----
echo ----- set permissions to certificates -----
echo -----
sudo addgroup eurydika_certs
sudo adduser influxdb eurydika_certs
sudo adduser grafana eurydika_certs
sudo chown influxdb:eurydika_certs /etc/ssl/sagittarius_eurydika_de.*
sudo systemctl restart influxdb

echo -----
echo ----- restore InfluxDB database -----
echo -----
sudo aws s3 cp s3://$deployment_bucket/backup_InfluxDB/ /home/ubuntu/backup_InfluxDB/ --recursive --no-progress
influxd restore -portable /home/ubuntu/backup_InfluxDB/
sudo rm -r /home/ubuntu/backup_InfluxDB/

echo -----
echo ----- configure InfluxDB users -----
echo -----
cmd='aws ssm get-parameters --region '$region' --names /Collector/parameters --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.InfluxDB.admin_uid'"'"''
admin_uid=$(eval $cmd)
cmd='aws ssm get-parameters --region '$region' --names /Collector/parameters --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.InfluxDB.admin_pw'"'"''
admin_pw=$(eval $cmd)
cmd='aws ssm get-parameters --region '$region' --names /Collector/parameters --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.database.user'"'"''
grafana_uid=$(eval $cmd)
cmd='aws ssm get-parameters --region '$region' --names /Collector/parameters --query '"'"'Parameters[0].Value'"'"' | jq '"'"'.|fromjson'"'"' | jq --raw-output '"'"'.database.password'"'"''
grafana_pw=$(eval $cmd)
influx -ssl -host sagittarius.eurydika.de -execute 'CREATE USER '$admin_uid' WITH PASSWORD '"'"$admin_pw"'"' WITH ALL PRIVILEGES'
influx -username $admin_uid -password $admin_pw -ssl -host sagittarius.eurydika.de -execute 'CREATE USER '$grafana_uid' WITH PASSWORD '"'"$grafana_pw"'"''
influx -username $admin_uid -password $admin_pw -ssl -host sagittarius.eurydika.de -execute 'USE TfL'
influx -username $admin_uid -password $admin_pw -ssl -host sagittarius.eurydika.de -execute 'GRANT ALL ON "TfL" TO "grafana"'
influx -username $admin_uid -password $admin_pw -ssl -host sagittarius.eurydika.de -execute 'SHOW USERS'

echo -----
echo ----- restore Grafana database -----
echo -----
sudo systemctl stop grafana-server
sudo aws s3 cp s3://$deployment_bucket/backup_Grafana/var/lib/ /var/lib/ --recursive --no-progress
sudo chown -R grafana:grafana /var/lib/grafana
sudo systemctl start grafana-server

echo -----
echo ----- set up backup -----
echo -----
sudo apt-get install zip -y
sudo aws s3 cp s3://$deployment_bucket/deployment/InfluxDB_Grafana_backup.sh /home/ubuntu/scripts/
sudo chmod +x /home/ubuntu/scripts/InfluxDB_Grafana_backup.sh
sudo aws s3 cp s3://$deployment_bucket/deployment/InfluxDB_Grafana_backup.crontab /home/ubuntu/scripts/
crontab -l | cat - /home/ubuntu/scripts/InfluxDB_Grafana_backup.crontab > crontab.txt && crontab crontab.txt
crontab -l

echo -----
echo ----- system restart to apply any updates that require reboot -----
echo -----
sudo shutdown -r now
