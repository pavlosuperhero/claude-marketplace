terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.12.2"

  backend "s3" {
    bucket       = "zippo-terraform-state-bucket"
    key          = "zippo-{{ENVIRONMENT}}"
    region       = "eu-central-1"
    encrypt      = false
    use_lockfile = true
  }
}

provider "aws" {
  region = var.region
}

provider "tls" {}
provider "archive" {}

module "aws_epam_ecs" {
  source = "../../iac/aws-epam-ecs"

  project               = var.project
  region                = var.region
  ecr_repo              = var.ecr_repo
  subnet_ids            = var.subnet_ids
  alb_sg_id             = var.alb_sg_id
  log_retention_in_days = var.log_retention_in_days

  create_dns_validation_records = var.create_dns_validation_records
  root_domain                   = var.root_domain
  zone_id                       = var.zone_id

  codebuild_projects                   = var.codebuild_projects
  codebuild_github_pat_secret_name     = var.codebuild_github_pat_secret_name
  codebuild_module_ssh_key_secret_name = var.codebuild_module_ssh_key_secret_name
}
