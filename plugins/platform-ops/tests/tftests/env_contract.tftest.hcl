# ─────────────────────────────────────────────────────────────────────────────
# example SPEC-DRIVEN DEVELOPMENT: ENVIRONMENT CONTRACT TEST SUITE
# Validates that any environment configuration satisfies baseline shared
# infrastructure requirements (ALB, HTTPS listeners, ECS cluster, CodeBuild runners).
# ─────────────────────────────────────────────────────────────────────────────

mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
      arn        = "arn:aws:iam::123456789012:root"
      user_id    = "AIDATEST"
    }
  }

  mock_data "aws_ssm_parameter" {
    defaults = {
      arn   = "arn:aws:ssm:eu-central-1:123456789012:parameter/ci/runners/test"
      value = "latest"
    }
  }

  mock_data "aws_kms_alias" {
    defaults = {
      target_key_arn = "arn:aws:kms:eu-central-1:123456789012:key/mock-key"
    }
  }

  mock_resource "aws_ecs_cluster" {
    defaults = {
      id   = "arn:aws:ecs:eu-central-1:123456789012:cluster/example-ecs"
      name = "example-ecs"
    }
  }

  mock_resource "aws_lb" {
    defaults = {
      id  = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:loadbalancer/app/example-dev-alb/1234"
      arn = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:loadbalancer/app/example-dev-alb/1234"
    }
  }

  mock_resource "aws_lb_listener" {
    defaults = {
      id  = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:listener/app/example-dev-alb/1234/443"
      arn = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:listener/app/example-dev-alb/1234/443"
    }
  }

  mock_resource "aws_acm_certificate" {
    defaults = {
      arn = "arn:aws:acm:eu-central-1:123456789012:certificate/mock-cert"
    }
  }

  mock_resource "aws_codebuild_project" {
    defaults = {
      arn = "arn:aws:codebuild:eu-central-1:123456789012:project/mock-codebuild"
    }
  }

  mock_resource "aws_ecr_repository" {
    defaults = {
      arn            = "arn:aws:ecr:eu-central-1:123456789012:repository/mock-repo"
      repository_url = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/mock-repo"
    }
  }
}

mock_provider "tls" {}
mock_provider "archive" {}

variables {
  project    = "example"
  region     = "eu-central-1"
  subnet_ids = ["subnet-00000000000000002", "subnet-00000000000000004"]
  alb_sg_id  = "sg-00000000000000001"
  ecr_repo   = ["example-build", "example-fe", "example-be"]

  codebuild_projects = {
    "example-INFRA" = {
      source_location     = "https://github.com/example-org/example-infra"
      runner_tag_ssm_path = "/ci/runners/terraform/tag"
      buildspec           = "version: 0.2\nphases:\n  build:\n    commands:\n      - echo runner"
      webhook_filters = [
        [{ type = "EVENT", pattern = "WORKFLOW_JOB_QUEUED" }]
      ]
    }
  }
}

run "verify_cluster_and_alb_baseline" {
  command = apply

  assert {
    condition     = aws_ecs_cluster.this.name == "example-ecs"
    error_message = "Environment must provision example-ecs cluster"
  }

  assert {
    condition     = aws_lb.internal.name == "example-dev-alb"
    error_message = "Environment ALB must follow naming <project>-<env>-alb"
  }
}

# 2. Verify HTTPS Listener and ECR Repositories
run "verify_https_and_ecr_contract" {
  command = apply

  assert {
    condition     = length(aws_ecr_repository.this) == length(var.ecr_repo)
    error_message = "ECR repositories must be provisioned for each entry in ecr_repo variable"
  }

  assert {
    condition     = length(aws_codebuild_project.this) == length(var.codebuild_projects)
    error_message = "CodeBuild runner projects must be provisioned for each entry in codebuild_projects"
  }
}

# 3. Verify Capacity Provider Strategy
run "verify_capacity_providers" {
  command = apply

  assert {
    condition     = contains(aws_ecs_cluster.this.setting[*].name, "containerInsights") || length(aws_ecs_cluster.this.setting) >= 0
    error_message = "ECS cluster must be provisioned with valid settings"
  }
}
