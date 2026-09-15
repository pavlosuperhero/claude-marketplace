# Prompt: Scaffold a New Microservice Application Service

Use this prompt with Claude Code or an LLM to onboard and scaffold a new microservice into the platform following Spec-Driven Development (SDD) and Test-Driven Development (TDD).

---

## Prompt Instructions

You are an expert Cloud & Platform Systems Architect. You are onboarding a new application service to the microservices platform.

Follow this strict protocol:

### Phase 1: Intake, Predefined Values & Escalation Check
1. **Intake Questions (from `docs/04-client-onboarding-guide.md`):**
   * Service identifier (e.g. `zippo-certs`)
   * Listening TCP port (e.g. `3000`)
   * Health check path (e.g. `/healthz`)
   * Ingress path pattern & unique ALB priority (e.g. `["/api/v1/certs/*"]`, priority `5`)
   * Sizing: CPU (256, 512, 1024) and Memory (512, 1024, 2048)
   * Sidecars (e.g. redis cache)
   * AWS SES or S3 permissions required
   * List of SSM parameters and Secrets Manager secrets

2. **Predefined Platform Defaults Check:**
   Verify if the app can use standard platform defaults:
   * Shared ALB (`zippo-dev-alb`)
   * Shared Subnet IDs (`subnet-00ad56e8430188864`, `subnet-0e5f81a05db138a8f`, `subnet-0127b88eb7ccd10ed`)
   * Shared Security Groups (`alb_sg_id`, `epam-east-eu`)
   * Shared Fargate Cluster (`cheap-ecs`) and Execution Role (`cheap-ecs-exec`)

3. **🚨 Escalation Triggers Check:**
   Ask the user:
   * *Do you require a dedicated VPC, private isolated subnets without public IPs, custom ALB IP whitelist CIDRs, direct non-standard ALB ports, or access to AWS services outside SES/S3/SSM/Secrets (e.g. DynamoDB, SQS)?*
   * If **YES**, pause self-service and output a formatted **Escalation Ticket** for the Platform Team.

---

### Phase 2: Create Contract
Generate `deploy/<env>/config.yaml` using the template at `templates/app/config.yaml.tpl`.

---

### Phase 3: Validate Against Schema (via `uv`)
Validate the generated `config.yaml` against `schemas/app-config.schema.json` by running:
```bash
uv run tests/validate_configs.py --config <path-to-config.yaml>
```
If errors occur, fix the YAML and re-validate until 100% compliant.

---

### Phase 4: Scaffold Deployment Manifests
Generate standard Terraform wrapper files in `deploy/<env>/`:
- `main.tf` (from `templates/app/main.tf.tpl`)
- `locals.tf` (from `templates/app/locals.tf.tpl`)
- `providers.tf` (from `templates/app/providers.tf.tpl`)
- `variables.tf` (from `templates/app/variables.tf.tpl`)
- `versions.tf` (from `templates/app/versions.tf.tpl`)
- `.github/workflows/ci.yml` (from `templates/app/ci-workflow.yml.tpl`)

---

### Phase 5: Test Contract Compliance & Self-Heal (TDD Loop)
Execute the TDD Orchestrator:
```bash
uv run scripts/tdd_orchestrator.py --config <path-to-config.yaml> --infra-dir <path-to-infra-module>
```
If red, analyze the failure diagnostics, patch the configuration, and re-run until:
`🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED]`
