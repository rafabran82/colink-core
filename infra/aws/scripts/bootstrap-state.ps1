<#
.SYNOPSIS
  Bootstrap per-environment state buckets and DynamoDB lock table.
  NOTE: Run with an AWS profile that can create S3 + DynamoDB in the target account.
#>
param(
  [ValidateSet("dev","staging","prod")] [string]$Env = "dev",
  [string]$Region = "us-east-1",
  [string]$BucketPrefix = "colink-tf-backend"
)

$Bucket = "$BucketPrefix-$Env"
Write-Host "Creating S3 bucket: $Bucket ($Region)"
aws s3api create-bucket --bucket $Bucket --create-bucket-configuration LocationConstraint=$Region 2>$null | Out-Null
aws s3api put-bucket-versioning --bucket $Bucket --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket $Bucket --server-side-encryption-configuration `
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

$table="colink-tf-locks"
Write-Host "Ensuring DynamoDB lock table: $table"
aws dynamodb create-table --table-name $table `
  --attribute-definitions AttributeName=LockID,AttributeType=S `
  --key-schema AttributeName=LockID,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST 2>$null | Out-Null
Write-Host "Done."

