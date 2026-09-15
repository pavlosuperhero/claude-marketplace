module "app" {
  source = "git::https://github.com/epddp/ZIPPO-INFR.git//iac/aws-epam-ecs-app?ref=main"

  project        = "{{PROJECT_NAME}}"
  region         = var.region
  service_name   = "{{SERVICE_ID}}"
  service_config = local.config
  desired_count  = var.desired_count
}
