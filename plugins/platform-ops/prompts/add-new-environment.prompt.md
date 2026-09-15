# Prompt: Add a New example Infrastructure Environment

Use this prompt with Claude Code or an LLM to provision and configure a new deployment environment (e.g. `stage`, `prod`, `qa`, `preview`) on the example platform.

---

## Prompt Instructions

You are an expert Cloud & Platform Systems Architect. You are creating a new environment for the example platform following Spec-Driven Development (SDD) and Test-Driven Development (TDD).

Follow this strict protocol:

### Phase 1: Environment Intake
Obtain or confirm the environment parameters:
1. Environment name (`stage`, `prod`, `qa`, `preview`)
2. AWS Region (default: `eu-central-1`)
3. Subnet IDs (minimum 2 in different AZs)
4. ALB Security Group ID
5. Custom Domain / Route 53 zone ID & root domain (e.g. `stage.example.com`)
6. CodeBuild GitHub PAT secret name & module deploy SSH key secret name

### Phase 2: Scaffold Environment in `example-INFR/lifecycle/<env>/`
Generate the environment configuration:
- `main.tf` (from `example-specs/templates/env/lifecycle-main.tf.tpl`)
- `terraform.tfvars` (from `example-specs/templates/env/terraform.tfvars.tpl`)
- `variables.tf`

### Phase 3: Verify Schema & Contracts
Validate against `example-specs/schemas/environment.schema.json`.
Run the environment contract test:
```bash
terraform -chdir=example-INFR/iac/ecs-environment-module test
```

### Phase 4: Generate Environment Manifests for All Microservices
For each active microservice (`example-BE`, `example-FE`, etc.), scaffold `deploy/<env>/`:
- `config.yaml` with environment-specific URLs and parameters
- `main.tf`, `locals.tf`, `providers.tf`, `variables.tf`, `versions.tf`
- Run `validate_configs.py` to ensure zero drift.
