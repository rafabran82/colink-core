variable "env"        { type = string }
variable "aws_region" { type = string }
variable "tags"       { type = map(string) }

# TODO: CloudWatch alarms, Log groups, X-Ray/OpenTelemetry wiring, dashboards
