rem create deployment S3 bucket
aws cloudformation create-stack --stack-name DeploymentBucket --template-body file://deployment_files/DeploymentBucket.yaml --profile workaccount

rem upload files required for deployment
"C:\Program Files\7-Zip\7z.exe" a -r deployment_files\lambda_collector.zip ..\collector\*
aws s3 cp deployment_files s3://collector-deployment-bucket-m1mgfnap/deployment --recursive --sse AES256 --profile workaccount

rem Upload security files (e.g. certificates) required for deployment that are stored outside
rem the code repository.
aws s3 cp ..\..\_secure_configs\collector\deployment_files s3://collector-deployment-bucket-m1mgfnap/deployment --recursive --sse AES256 --profile workaccount

rem copies of InfluxDb and Grafana database backups need to be copied manually to the
rem deployment S3 bucket
