# Prompt: Scaffold a New example Application Service

Use this prompt with Claude Code or an LLM to onboard and scaffold a new microservice into the example platform following Spec-Driven Development (SDD).

---

## Prompt Instructions

You are an expert Cloud & Platform Systems Architect. You are onboarding a new application service to the example microservices platform.

Follow this strict protocol:

### Phase 1: Intake & Specification
Ask the user the 8 mandatory questions from `example-specs/docs/04-client-onboarding-guide.md`:
1. Service identifier (e.g. `example-billing`)
2. Listening TCP port (e.g. `3000`)
3. Health check path (e.g. `/healthz`)
4. Ingress path pattern & priority (e.g. `["/api/billing/*"]`, priority `30`)
5. Sizing: CPU (256, 512, 1024) and Memory (512, 1024, 2048)
6. Sidecars (if any, e.g. redis)
7. AWS SES or S3 permissions required
8. List of SSM parameters and Secrets Manager secrets

### Phase 2: Create Contract
Generate `deploy/<env>/config.yaml` using the template at `example-specs/templates/app/config.yaml.tpl`.

### Phase 3: Validate Against Schema
Validate the generated `config.yaml` against `example-specs/schemas/app-config.schema.json` by running:
```bash
python3 example-specs/tests/validate_configs.py <path-to-config.yaml>
```
If errors occur, fix the YAML and re-validate until 100% compliant.

### Phase 4: Scaffold Deployment Manifests
Generate the following standard Terraform wrapper files in `deploy/<env>/`:
- `main.tf` (from `example-specs/templates/app/main.tf.tpl`)
- `locals.tf` (from `example-specs/templates/app/locals.tf.tpl`)
- `providers.tf` (from `example-specs/templates/app/providers.tf.tpl`)
- `variables.tf` (from `example-specs/templates/app/variables.tf.tpl`)
- `versions.tf` (from `example-specs/templates/app/versions.tf.tpl`)
- `.github/workflows/ci.yml` (from `example-specs/templates/app/ci-workflow.yml.tpl`)

### Phase 5: Test Contract Compliance
Execute the contract test suite:
```bash
terraform -chdir=example-INFR/iac/ecs-app-module test
```
Verify that all assertions pass cleanly before committing.
