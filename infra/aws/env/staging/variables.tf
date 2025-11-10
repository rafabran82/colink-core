variable "env"         { type = string }
variable "aws_region"  { type = string }
variable "aws_profile" { type = string }
variable "tags" {
  type = map(string)
  default = {}
}
