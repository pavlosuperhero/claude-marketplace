---
description: Run Layer 3 Plan Verification (terraform plan) against deploy/dev manifests to preview changes before applying
---

Run Layer 3 Plan Verification on the deployment manifests:

1. Identify the target deployment folder (e.g. `deploy/dev`).
2. Run `terraform fmt -check` and `terraform validate` inside that directory.
3. Run `terraform plan` (or `terraform plan -no-color`) to generate a dry-run preview of resources to be added, changed, or destroyed.
4. Output a concise table of planned changes:
   - ECS Service and Task Definition
   - ALB Target Groups and Listener Rules
   - IAM Roles and Policy Attachments
   - CloudWatch Log Groups
