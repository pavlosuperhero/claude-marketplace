module "app" {
  source = "{{APP_MODULE_SOURCE}}"

  project        = "{{PROJECT_NAME}}"
  region         = var.region
  service_name   = "{{SERVICE_ID}}"
  service_config = local.config
  desired_count  = var.desired_count
}
