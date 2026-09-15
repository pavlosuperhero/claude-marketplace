# 05. Environment Guide (Provisioning New Environments)

This guide provides the procedure for adding and configuring a new environment (e.g., `stage`, `prod`, `qa`, or an ephemeral `preview` environment) to the ZIPPO platform.

---

## 1. Environment Architecture Principles

Each environment maintains:
1. **Isolated Terraform State:** Stored under `zippo-terraform-state-bucket` with key `zippo-<env>` for platform infrastructure and `<service>-<env>` for application services.
2. **Dedicated Shared ALB:** Following the naming convention `<project>-<env>-alb` (e.g. `zippo-stage-alb`, `zippo-prod-alb`).
3. **Dedicated Subnets & Security Groups:** Or shared VPC with isolated private subnets.
4. **Environment-Scoped Parameters:** Systems Manager parameters partitioned by prefix or account boundary.

---

## 2. Step-by-Step Environment Provisioning

### Step 1: Create the Environment Directory in `ZIPPO-INFR`
Create `ZIPPO-INFR/lifecycle/<env>/`:
* `main.tf`: Instantiates `module "aws_epam_ecs"` targeting the new environment backend state.
* `terraform.tfvars`: Declares subnet IDs, ALB security group, ACM domain, and CodeBuild projects for the new environment.
* `variables.tf`: Inherits standard variables.

### Step 2: Validate Environment Specification
Run the schema validation against `schemas/environment.schema.json` and execute the environment contract test:
```bash
terraform -chdir=zippo-specs/tests/tftests test -filter=env_contract.tftest.hcl
```

### Step 3: Terraform Apply Infrastructure
Run `terraform apply` to provision:
* The environment ECS cluster (`zippo-<env>-ecs` or `cheap-ecs`).
* The environment ALB with HTTPS listener and ACM certificate.
* The environment CodeBuild runner projects and webhooks.

### Step 4: Seed App Configurations
For each active microservice (`ZIPPO-BE`, `ZIPPO-FE`, etc.):
* Create `deploy/<env>/config.yaml` populated with environment-specific URLs, database names, and routing priorities.
* Create `deploy/<env>/main.tf`, `locals.tf`, `providers.tf`, `variables.tf`, and `versions.tf`.
* Populate secrets in AWS Secrets Manager and parameters in AWS SSM.
* Trigger initial deployment.
