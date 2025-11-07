# Example wiring of modules (expand later)

module "network" {
  source      = "../../modules/network"
  env         = var.env
  aws_region  = var.aws_region
  tags        = var.tags
}

module "compute" {
  source      = "../../modules/compute"
  env         = var.env
  aws_region  = var.aws_region
  vpc_id      = module.network.vpc_id
  private_subnets = module.network.private_subnets
  tags        = var.tags
}

module "observability" {
  source     = "../../modules/observability"
  env        = var.env
  aws_region = var.aws_region
  tags       = var.tags
}
