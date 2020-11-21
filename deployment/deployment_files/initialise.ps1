# create deployment S3 bucket
$stack_name = "CollectorDeploymentBucket"
aws cloudformation create-stack --stack-name $stack_name --template-body file://$PSScriptRoot/DeploymentBucket.yaml --profile workaccount

# Wait for stack creation to cpmplete
Write-Host "Waiting for stack creation to complete ..."
$max_count = 12
$count = 0
$done = $false
While ((-Not $done) -And (-Not ($count -ge $max_count))) {
    Start-Sleep -Seconds 5
    $status = aws cloudformation describe-stacks --stack-name $stack_name --query "Stacks[0].StackStatus" --output text --profile workaccount
    Write-Host "stack status: " $status
    $done = $status.Substring($status.Length - "COMPLETE".Length).Equals("COMPLETE")
    $count = $count + 1
}

# get the name of the S3 bucket just crteated
$DeploymentBucket = (aws ssm get-parameters --names /Collector/deployment/S3bucket --query "Parameters[0].Value" --output text --profile workaccount)
Write-Host "Deployment S3 bucket name: " $DeploymentBucket

# upload files required for deployment
& 'C:\Program Files\7-Zip\7z.exe' a -r $PSScriptRoot\lambda_collector.zip $PSScriptRoot\..\..\collector\*
aws s3 cp $PSScriptRoot s3://$DeploymentBucket/deployment --recursive --sse AES256 --profile workaccount

# Upload security files (e.g. certificates) required for deployment that are stored outside
# the code repository.
aws s3 cp $PSScriptRoot\..\..\..\_secure_configs\collector\deployment_files s3://$DeploymentBucket/deployment --recursive --sse AES256 --profile workaccount

# copies of InfluxDb and Grafana database backups need to be copied manually to the
# deployment S3 bucket

Write-Host "Script completed."

