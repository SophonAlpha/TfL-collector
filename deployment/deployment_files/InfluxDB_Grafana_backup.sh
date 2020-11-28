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
echo ----- backup InfluxDB -----
echo -----
influxd backup -portable /home/ubuntu/backup_InfluxDB/
aws s3 cp /home/ubuntu/backup_InfluxDB/ s3://$backup_bucket/backup_InfluxDB_$backup_time/ --sse AES256 --recursive --no-progress
rm -r /home/ubuntu/backup_InfluxDB/

echo -----
echo ----- backup Grafana -----
echo -----
sudo aws s3 sync /var/lib/grafana/ s3://$backup_bucket/backup_Grafana_$backup_time/var/lib/grafana/ --sse AES256 --no-progress
sudo aws s3 sync /var/log/grafana/ s3://$backup_bucket/backup_Grafana_$backup_time/var/log/grafana/ --sse AES256 --no-progress
sudo aws s3 sync /etc/grafana/ s3://$backup_bucket/backup_Grafana_$backup_time/etc/grafana/ --sse AES256 --no-progress

echo -----
echo ----- backup completed -----
echo -----
