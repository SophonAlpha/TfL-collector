#!/bin/bash

#example:
#  ./backup_to_deployment.sh s3://collector-backupbucket-z76b428yurqz-backupbucket-1j3r1h64sww80/backup_InfluxDB/InfluxDB_backup_2020-11-29_11-57-12.zip InfluxDB_backup_2020-11-29_11-57-12.zip home/ubuntu/backup_InfluxDB/ s3://collectordeploymentbucket-deploymentbucket-ke28k5jehn4d/backup_InfluxDB/

source_S3_URI=$1
source_zip_file=$2
target_folder=$3
target_S3_URI=$4

aws s3 cp $source_S3_URI .
unzip $source_zip_file
aws s3 cp $target_folder $target_S3_URI --recursive --sse AES256
