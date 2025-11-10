variable "env"        { type = string }
variable "aws_region" { type = string }
variable "tags"       { type = map(string) }

# TODO: KMS keys, Secrets Manager, least-privilege IAM roles/policies
