# Prompt: Add a New Platform Infrastructure Environment

Use this prompt with Claude Code or an LLM to provision and configure a new deployment environment (e.g. `stage`, `prod`, `qa`, `preview`) on your platform.

---

## Prompt Instructions

You are an expert Cloud & Platform Systems Architect. You are creating a new environment for your platform following Spec-Driven Development (SDD) and Test-Driven Development (TDD).

Follow this strict protocol:

### Phase 1: Environment Intake
Obtain or confirm the environment parameters:
1. Environment name (`stage`, `prod`, `qa`, `preview`)
2. AWS region and Terraform state bucket, key, and region
3. Subnet IDs (minimum 2 in different AZs)
4. ALB Security Group ID
5. Custom Domain / Route 53 zone ID & root domain (e.g. `stage.example.com`)
6. CodeBuild GitHub PAT secret name and module deploy SSH key secret name
7. Project name, environment module source, infrastructure repository URL, ECR repository list, CodeBuild project name, and runner tag SSM path. See [Configuration](../README.md#configuration).

### Phase 2: Scaffold Environment in `<infra-repo>/lifecycle/<env>/`
Generate the environment configuration:
- `main.tf` (from `templates/env/lifecycle-main.tf.tpl`)
- `terraform.tfvars` (from `templates/env/terraform.tfvars.tpl`)
- `variables.tf`

### Phase 3: Verify Schema & Contracts
Validate against `schemas/environment.schema.json`.
Run the environment contract test:
```bash
terraform -chdir=/path/to/env-module test
```

### Phase 4: Generate Environment Manifests for All Microservices
For each active microservice (`backend`, `frontend`, etc.), scaffold `deploy/<env>/`:
- `config.yaml` with environment-specific URLs and parameters
- `main.tf`, `locals.tf`, `providers.tf`, `variables.tf`, `versions.tf`
- Run `validate_configs.py` to ensure zero drift.
