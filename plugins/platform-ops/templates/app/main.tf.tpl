module "app" {
  source = "git::https://github.com/example-org/example-infra.git//iac/ecs-app-module?ref=main"

  project        = "{{PROJECT_NAME}}"
  region         = var.region
  service_name   = "{{SERVICE_ID}}"
  service_config = local.config
  desired_count  = var.desired_count
}
