---
description: Format all Terraform and HCL files to canonical style (terraform fmt)
---

Format all Terraform configuration files in the project:

1. Locate all directories containing `.tf` files (e.g. `deploy/dev`, `deploy/prd`).
2. Execute `terraform fmt -recursive` on each directory.
3. Report any files that were reformatted.
