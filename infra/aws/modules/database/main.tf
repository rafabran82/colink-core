variable "env"        { type = string }
variable "aws_region" { type = string }
variable "tags"       { type = map(string) }

# TODO: RDS/Aurora or DynamoDB; parameter groups; backups; rotation
