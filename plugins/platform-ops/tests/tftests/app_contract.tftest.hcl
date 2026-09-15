# ─────────────────────────────────────────────────────────────────────────────
# ZIPPO SPEC-DRIVEN DEVELOPMENT: APP CONTRACT TEST SUITE
# Validates that any application service_config fulfills the ECS Fargate,
# ALB Ingress, CloudWatch, and IAM task contract.
# ─────────────────────────────────────────────────────────────────────────────

mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
      arn        = "arn:aws:iam::123456789012:root"
      user_id    = "AIDATEST"
    }
  }

  mock_data "aws_vpc" {
    defaults = {
      id         = "vpc-mock001"
      cidr_block = "10.0.0.0/16"
    }
  }

  mock_data "aws_subnets" {
    defaults = {
      ids = ["subnet-mock001", "subnet-mock002"]
    }
  }

  mock_data "aws_ecs_cluster" {
    defaults = {
      id  = "arn:aws:ecs:eu-central-1:123456789012:cluster/cheap-ecs"
      arn = "arn:aws:ecs:eu-central-1:123456789012:cluster/cheap-ecs"
    }
  }

  mock_data "aws_iam_role" {
    defaults = {
      arn  = "arn:aws:iam::123456789012:role/cheap-ecs-exec"
      name = "cheap-ecs-exec"
    }
  }

  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }

  mock_data "aws_security_group" {
    defaults = {
      id = "sg-mocktasks"
    }
  }

  mock_data "aws_lb" {
    defaults = {
      arn  = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:loadbalancer/app/zippo-dev-alb/1234"
      name = "zippo-dev-alb"
    }
  }

  mock_data "aws_lb_listener" {
    defaults = {
      arn             = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:listener/app/zippo-dev-alb/1234/5678"
      certificate_arn = "arn:aws:acm:eu-central-1:123456789012:certificate/mock-cert"
    }
  }

  mock_data "aws_ssm_parameter" {
    defaults = {
      arn   = "arn:aws:ssm:eu-central-1:123456789012:parameter/ci/zippo-app/image_tag"
      value = "v1.0.0-mock"
      type  = "String"
    }
  }

  mock_data "aws_secretsmanager_secret" {
    defaults = {
      arn  = "arn:aws:secretsmanager:eu-central-1:123456789012:secret:mock-secret"
      name = "mock-secret"
    }
  }

  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/mock-role"
      id  = "mock-role"
    }
  }

  mock_resource "aws_iam_role_policy" {
    defaults = {
      id = "mock-inline-policy"
    }
  }

  mock_resource "aws_ecs_task_definition" {
    defaults = {
      arn = "arn:aws:ecs:eu-central-1:123456789012:task-definition/zippo-app:1"
    }
  }

  mock_resource "aws_ecs_service" {
    defaults = {
      id = "mock-service"
    }
  }

  mock_resource "aws_cloudwatch_log_group" {
    defaults = {
      arn = "arn:aws:logs:eu-central-1:123456789012:log-group:/ecs/zippo-app:*"
    }
  }

  mock_resource "aws_lb_target_group" {
    defaults = {
      arn = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:targetgroup/mock-tg/1234"
      id  = "mock-tg"
    }
  }

  mock_resource "aws_lb_listener_rule" {
    defaults = {
      arn = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:listener-rule/app/mock/1234"
      id  = "mock-rule"
    }
  }

  mock_resource "aws_lb_listener" {
    defaults = {
      arn = "arn:aws:elasticloadbalancing:eu-central-1:123456789012:listener/app/mock/direct"
      id  = "mock-direct-listener"
    }
  }
}

variables {
  project        = "zippo"
  region         = "eu-central-1"
  service_name   = "zippo-app"
  service_config = {
    name = "contract-test-app"
    port = 8080
    alb = {
      health_check  = "/healthz"
      path_patterns = ["/api/v2/*"]
      priority      = 50
    }
  }
}

# 1. Verify Task Role Name & Boundary
run "verify_task_role_contract" {
  command = apply

  assert {
    condition     = aws_iam_role.task.name == "cheap-ecs-contract-test-app-task"
    error_message = "Task role must follow convention <cluster>-<service_config.name>-task"
  }

  assert {
    condition     = aws_iam_role.task.permissions_boundary == "arn:aws:iam::123456789012:policy/eo_role_boundary"
    error_message = "Task role must enforce EPAM eo_role_boundary"
  }
}

# 2. Verify Fargate ECS Service Configuration
run "verify_ecs_service_contract" {
  command = apply

  assert {
    condition     = aws_ecs_service.this.launch_type == "FARGATE"
    error_message = "Service must run on AWS FARGATE launch type"
  }

  assert {
    condition     = aws_ecs_service.this.network_configuration[0].assign_public_ip == true
    error_message = "Service tasks must assign public IP in default VPC"
  }
}

# 3. Verify Target Group and Health Check Contract
run "verify_target_group_contract" {
  command = apply

  assert {
    condition     = aws_lb_target_group.this.target_type == "ip"
    error_message = "Target group target_type must be 'ip' for awsvpc Fargate tasks"
  }

  assert {
    condition     = aws_lb_target_group.this.health_check[0].path == "/healthz"
    error_message = "Target group health check path must match service_config.alb.health_check"
  }
}

# 4. Verify ALB Ingress Routing Listener Rule
run "verify_listener_rule_contract" {
  command = apply

  assert {
    condition     = length(aws_lb_listener_rule.this) == 1
    error_message = "Listener rule must be provisioned when alb.path_patterns is provided"
  }

  assert {
    condition     = aws_lb_listener_rule.this[0].priority == 50
    error_message = "Listener rule priority must match service_config.alb.priority"
  }
}

# 5. Verify Sidecar Container Integration
run "verify_sidecar_contract" {
  command = apply

  variables {
    service_config = {
      name = "contract-with-sidecar"
      port = 8080
      sidecars = [
        {
          name      = "cache"
          ecr_image = "zippo-build:redis-alpine"
        }
      ]
    }
  }

  assert {
    condition     = strcontains(aws_ecs_task_definition.this.container_definitions, "cache")
    error_message = "Task definition must serialize defined sidecar containers"
  }
}
