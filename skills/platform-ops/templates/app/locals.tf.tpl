locals {
  config_raw = yamldecode(file("${path.module}/config.yaml"))
  config     = { for k, v in local.config_raw : lower(k) => v }
}
