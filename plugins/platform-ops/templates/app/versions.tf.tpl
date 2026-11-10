terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0.0"
    }
  }
  required_version = ">= 1.12.2"

  backend "s3" {
    bucket       = "{{STATE_BUCKET}}"
    key          = "{{STATE_KEY}}"
    region       = "{{STATE_REGION}}"
    encrypt      = true
    use_lockfile = true
  }
}
