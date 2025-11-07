# Fill these per env before `terraform init -backend-config=...`
bucket  = "colink-tf-backend-dev"
key     = "state/dev/colink.tfstate"
region  = "us-east-1"
encrypt = true
dynamodb_table = "colink-tf-locks"
