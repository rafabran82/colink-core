# Fill these per env before `terraform init -backend-config=...`
bucket  = "colink-tf-backend-prod"
key     = "state/prod/colink.tfstate"
region  = "us-east-1"
encrypt = true
dynamodb_table = "colink-tf-locks"
