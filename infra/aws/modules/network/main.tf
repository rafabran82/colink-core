variable "env"        { type = string }
variable "aws_region" { type = string }
variable "tags"       { type = map(string) }

# TODO: create VPC + subnets + routing; export IDs
output "vpc_id"          { value = "vpc-PLACEHOLDER" }
output "private_subnets" { value = ["subnet-a", "subnet-b"] }
