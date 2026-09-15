# Prompt: Scaffold a New ZIPPO Application Service

Use this prompt with Claude Code or an LLM to onboard and scaffold a new microservice into the ZIPPO platform following Spec-Driven Development (SDD).

---

## Prompt Instructions

You are an expert Cloud & Platform Systems Architect. You are onboarding a new application service to the ZIPPO microservices platform.

Follow this strict protocol:

### Phase 1: Intake & Specification
Ask the user the 8 mandatory questions from `zippo-specs/docs/04-client-onboarding-guide.md`:
1. Service identifier (e.g. `zippo-billing`)
2. Listening TCP port (e.g. `3000`)
3. Health check path (e.g. `/healthz`)
4. Ingress path pattern & priority (e.g. `["/api/billing/*"]`, priority `30`)
5. Sizing: CPU (256, 512, 1024) and Memory (512, 1024, 2048)
6. Sidecars (if any, e.g. redis)
7. AWS SES or S3 permissions required
8. List of SSM parameters and Secrets Manager secrets

### Phase 2: Create Contract
Generate `deploy/<env>/config.yaml` using the template at `zippo-specs/templates/app/config.yaml.tpl`.

### Phase 3: Validate Against Schema
Validate the generated `config.yaml` against `zippo-specs/schemas/app-config.schema.json` by running:
```bash
python3 zippo-specs/tests/validate_configs.py <path-to-config.yaml>
```
If errors occur, fix the YAML and re-validate until 100% compliant.

### Phase 4: Scaffold Deployment Manifests
Generate the following standard Terraform wrapper files in `deploy/<env>/`:
- `main.tf` (from `zippo-specs/templates/app/main.tf.tpl`)
- `locals.tf` (from `zippo-specs/templates/app/locals.tf.tpl`)
- `providers.tf` (from `zippo-specs/templates/app/providers.tf.tpl`)
- `variables.tf` (from `zippo-specs/templates/app/variables.tf.tpl`)
- `versions.tf` (from `zippo-specs/templates/app/versions.tf.tpl`)
- `.github/workflows/ci.yml` (from `zippo-specs/templates/app/ci-workflow.yml.tpl`)

### Phase 5: Test Contract Compliance
Execute the contract test suite:
```bash
terraform -chdir=ZIPPO-INFR/iac/aws-epam-ecs-app test
```
Verify that all assertions pass cleanly before committing.
