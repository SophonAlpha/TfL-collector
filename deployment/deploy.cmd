rem create deployment S3 bucket
aws cloudformation create-stack --stack-name DeploymentBucket --template-body file://DeploymentBucket.yaml --profile workaccount

rem upload files required for deployment
aws s3 cp deployment_files s3://collector-deployment-bucket-m1mgfnap/deployment --recursive --sse AES256 --profile workaccount
aws s3 cp ..\..\_secure_configs\collector s3://collector-deployment-bucket-m1mgfnap/deployment --recursive --exclude "*" --include "sagittarius_eurydika_de.*" --sse AES256 --profile workaccount
