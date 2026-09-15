locals {
  config_raw = yamldecode(file("${path.module}/config.yaml"))

  # Normalize all keys to lowercase recursively (top-level + nested objects)
  config = { for k, v in local.config_raw : lower(k) => (
    can(tomap(v)) ? { for nk, nv in v : lower(nk) => nv } : v
  ) }
}
