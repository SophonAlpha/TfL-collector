#!/bin/bash
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo -----
echo ----- backup started -----
echo -----

# get parameters
region=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq --raw-output .region)
cmd='aws ssm get-parameters --region '$region' --names /Collector/backup/S3bucket --query '"'"'Parameters[0].Value'"'"' --output text'
backup_bucket=$(eval $cmd)
backup_time=$(eval 'date +%Y-%m-%d_%H-%M-%S')

echo -----
echo ----- remove previous local backup files -----
echo -----
rm -r /home/ubuntu/backup_InfluxDB/
rm -r /home/ubuntu/backup/
mkdir /home/ubuntu/backup

echo -----
echo ----- backup InfluxDB -----
echo -----
influxd backup -portable /home/ubuntu/backup_InfluxDB/
zip -r -m /home/ubuntu/backup/backup_InfluxDB.zip /home/ubuntu/backup_InfluxDB/*
aws s3 cp /home/ubuntu/backup/backup_InfluxDB.zip s3://$backup_bucket/backup_InfluxDB/InfluxDB_backup_$backup_time.zip --sse AES256 --no-progress

echo -----
echo ----- backup Grafana -----
echo -----
sudo zip -r /home/ubuntu/backup/backup_Grafana.zip /var/lib/grafana/*
sudo zip -r /home/ubuntu/backup/backup_Grafana.zip /var/log/grafana/*
sudo zip -r /home/ubuntu/backup/backup_Grafana.zip /etc/grafana/*
aws s3 cp /home/ubuntu/backup/backup_Grafana.zip s3://$backup_bucket/backup_Grafana/backup_Grafana_$backup_time.zip --sse AES256 --no-progress

echo -----
echo ----- backup completed -----
echo -----
