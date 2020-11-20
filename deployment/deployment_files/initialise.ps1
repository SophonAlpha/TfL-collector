# create deployment S3 bucket
aws cloudformation create-stack --stack-name CollectorDeploymentBucket --template-body file://$PSScriptRoot/DeploymentBucket.yaml --profile workaccount



$DeploymentBucket = (aws ssm get-parameters --names /Collector/deployment/S3bucket --query "Parameters[0].Value" --profile workaccount)
$DeploymentPrefix = (aws ssm get-parameters --names /Collector/deployment/prefix --query "Parameters[0].Value" --profile workaccount)

# upload files required for deployment
& 'C:\Program Files\7-Zip\7z.exe' a -r $PSScriptRoot\lambda_collector.zip $PSScriptRoot\..\..\collector\*
aws s3 cp $PSScriptRoot s3://$DeploymentBucket/$DeploymentPrefix --recursive --sse AES256 --profile workaccount

# Upload security files (e.g. certificates) required for deployment that are stored outside
# the code repository.
aws s3 cp $PSScriptRoot\..\..\..\_secure_configs\collector\deployment_files s3://$DeploymentBucket/$DeploymentPrefix --recursive --sse AES256 --profile workaccount

# copies of InfluxDb and Grafana database backups need to be copied manually to the
# deployment S3 bucket

