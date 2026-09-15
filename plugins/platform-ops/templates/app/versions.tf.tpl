terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0.0"
    }
  }
  required_version = ">= 1.12.2"

  backend "s3" {
    bucket       = "zippo-terraform-state-bucket"
    key          = "{{SERVICE_ID}}"
    region       = "eu-central-1"
    encrypt      = false
    use_lockfile = true
  }
}
