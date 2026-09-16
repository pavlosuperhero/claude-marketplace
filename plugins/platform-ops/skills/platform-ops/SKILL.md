---
name: platform-ops
description: Spec-Driven Development (SDD) and Test-Driven Development (TDD) engine for onboarding, templating, and deploying containerized Node.js microservices and cloud infrastructure environments on AWS ECS using central ECR artifactory, declarative contracts, JSON Schemas, and Terraform contract tests.
---

# Platform Operations Skill

This skill automates and governs the lifecycle of microservices and cloud infrastructure environments using **Spec-Driven Development (SDD)** and **Test-Driven Development (TDD)**.

---

## 0. Supported Stack & Predefined Baseline

> [!NOTE]
> **Currently Supported Stack:**
> * **Application Runtime:** **Node.js** projects (NestJS, Express, React/Nginx SSR) running inside **AWS ECS Fargate & Fargate Spot**.
> * **Build Artifactory:** Centralized **Amazon ECR** repositories (`<account-id>.dkr.ecr.<region>.amazonaws.com/<service>`) for release images and builder cache images (`zippo-build:*`).
> * **Ingress & Traffic:** AWS Application Load Balancer (ALB) with path-based HTTPS routing and target group health probes.
> * **Secrets & Configuration:** AWS Systems Manager (SSM) Parameter Store (plain and SecureString) and AWS Secrets Manager.
> * **CI/CD:** Ephemeral AWS CodeBuild runners integrated via GitHub Actions `WORKFLOW_JOB_QUEUED` webhooks.
> * **Dependency Management:** All Python helper tools and test runners execute via **`uv run`** without global environment pollution.

---

## 1. Core Documentation Map (Theme Pointers)

Before performing actions, refer to the authoritative specification documents:

* **Platform Architecture & Topology:** [01-architecture-overview.md](docs/01-architecture-overview.md)
* **Lifecycle vs. Application Boundaries:** [02-lifecycle-vs-app-roles.md](docs/02-lifecycle-vs-app-roles.md)
* **Continuous Deployment Workflow:** [03-deployment-process.md](docs/03-deployment-process.md)
* **Client Onboarding & Escalation Protocol:** [04-client-onboarding-guide.md](docs/04-client-onboarding-guide.md)
* **Environment Provisioning Guide:** [05-environment-guide.md](docs/05-environment-guide.md)
* **Spec-Driven Methodology:** [06-spec-driven-development.md](docs/06-spec-driven-development.md)
* **Test-Driven Infrastructure & Contracts:** [07-test-driven-development.md](docs/07-test-driven-development.md)
* **JSON Schema Definitions:** [app-config.schema.json](schemas/app-config.schema.json) | [service-spec.schema.json](schemas/service-spec.schema.json) | [environment.schema.json](schemas/environment.schema.json)

---

## 2. Standard Workflows

### Workflow A: Onboard a New Application Service
When a user asks to deploy or onboard a new application or microservice:

1. **Check for Additional Specifications (optional context enrichment):**
   * The primary spec source is **Confluence via MCP** (when available) or an explicitly configured `--specs-dir <path>` / `ADDITIONAL_SPECS_PATH` env var. Local directory auto-discovery (`Project_Specifications/`, `zippo-specs/`) is a convenience fallback hint — probed only if nothing else is configured.
   * If a specs directory is available, scan it for context. Look for:
     - **Networking/ingress docs** — existing ALB rule priorities and path patterns (hints only; authoritative answer is always the live sibling configs).
     - **Sizing/deployment docs** — CPU/memory baselines, desired replica counts, subnet guidance.
     - **IAM/security docs** — permission boundary requirements, allowed permission scopes.
   * Auto-fill known parameters from discovered context and only prompt the user for unique application-specific parameters.

2. **Intake & Escalation Check:**
   Prompt the user for the remaining intake answers in [04-client-onboarding-guide.md](docs/04-client-onboarding-guide.md):
   * Service identifier (`<service-name>`, kebab-case)
   * Container listening port (e.g. `3000`, `8080`) & health check path (e.g. `/healthz`)
   * Ingress path patterns (e.g. `["/api/<service>/*"]`) & unique ALB rule priority
   * Task sizing (CPU units, memory in MiB, desired replica count)
   * Sidecars (e.g. redis cache), SES/S3 permissions, SSM parameters, and secrets.
   * **🚨 ESCALATION TRIGGERS:** If the service requires non-default subnets, dedicated security group ingress CIDRs, dedicated direct ALB ports, or IAM permissions beyond SES/S3/SSM/Secrets (e.g., DynamoDB, SQS), pause self-service generation and output an **Escalation Request** for the Platform Team.

3. **Generate Specification Contract:**
   * Create `deploy/<env>/config.yaml` using the template at `templates/app/config.yaml.tpl`.

4. **Validate Against JSON Schema (via `uv`):**
   * Run the validator script with `uv run` (including `--specs-dir` check):
     ```bash
     uv run tests/validate_configs.py --config <target-repo>/deploy/<env>/config.yaml --specs-dir <local-specs-path>
     ```
   * Enforce schema compliance before generating or applying Terraform code.

5. **Scaffold Deployment Manifests:**
   * Generate `deploy/<env>/main.tf` from `templates/app/main.tf.tpl`.
   * Generate `locals.tf`, `providers.tf`, `variables.tf`, and `versions.tf`.
   * Generate CI/CD workflow from `templates/app/ci-workflow.yml.tpl`.

6. **Run Contract Tests & Self-Heal (TDD) — 🛑 MANDATORY HARDGATE:**
   * **DO NOT SKIP THIS STEP.** Generating files without executing tests is strictly prohibited.
   * You **MUST** execute the TDD orchestrator using your Bash tool:
     ```bash
     uv run scripts/tdd_orchestrator.py --config deploy/<env>/config.yaml
     ```
     *(Or pass `--specs-dir <path>` if custom local specs are used)*
   * The orchestrator validates all 3 TDD Layers:
     - **Layer 1 (Static Analysis & Linting):** Schema validation, `terraform fmt -check`, and `terraform validate`.
     - **Layer 2 (Contract Unit Tests):** Native `terraform test` assertions with mock AWS providers.
     - **Layer 3 (Plan Verification):** Dry-run `terraform plan` on `deploy/<env>` to preview resource changes before apply.
   * If the output is **RED**, analyze the diagnostics, self-heal `config.yaml` or Terraform wrappers, and re-execute.
   * You have **NOT** finished onboarding until all 3 layers pass:
     `🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED]`
   * The plugin's `Stop` hook will block you from completing if this step is skipped.
   * *(Tip: Users can also trigger `/verify`, `/plan`, or `/fmt` slash commands directly).*

---

### Workflow B: Add a New Infrastructure Environment
When adding or provisioning a new environment (`stage`, `prod`, `qa`, `preview`):

1. **Intake Phase:**
   Follow [05-environment-guide.md](docs/05-environment-guide.md) to gather VPC subnets, ALB security groups, and DNS/Route 53 parameters.

2. **Scaffold Lifecycle Platform:**
   * Create `lifecycle/<new-env>/main.tf` from `templates/env/lifecycle-main.tf.tpl`.
   * Create `terraform.tfvars` from `templates/env/terraform.tfvars.tpl`.

3. **Validate & Test:**
   * Validate against `schemas/environment.schema.json`.
   * Run environment contract tests:
     ```bash
     terraform -chdir=tests/tftests test -filter=env_contract.tftest.hcl
     ```

4. **Replicate Microservice Deployments:**
   * Scaffold `deploy/<new-env>/` across all microservices using verified templates.
   * Run `uv run tests/validate_configs.py --config <file>` across all created manifests.

---

### Workflow C: Add a New Secret or Environment Variable
Follow the dynamic provisioning pattern in [03-deployment-process.md](docs/03-deployment-process.md):
1. Add the variable or secret entry to `config.yaml` (`ENV_VARS` or `SECRETS`).
2. Run `uv run tests/validate_configs.py --config <path-to-config.yaml>`.
3. Provision the resource via the automated CI workflow dispatch in the infra repo.

---

### Workflow D: The Self-Healing TDD Loop (AI Orchestrator)
When generating, validating, or fixing configurations against failing tests:

1. **Trigger Orchestrator Runner via `uv`:**
   Run the visual TDD orchestrator with CLI flags (automatically discovers local specs or pass `--specs-dir`):
   ```bash
   uv run scripts/tdd_orchestrator.py --config <path-to-config.yaml> --infra-dir <path-to-infra-module> [--specs-dir <path-to-local-specs>]
   ```

2. **Diagnose Failures (Red State):**
   * If **Schema Violation:** Inspect reported missing properties, disallowed port ranges, or malformed SSM paths against `schemas/app-config.schema.json`.
   * If **Terraform Assertion Failure:** Read the failed assertion from `tests/tftests/*.tftest.hcl` (e.g., ALB routing rule priority collision, missing health check path, or ungranted S3/SES permissions).

3. **Apply Surgical Patch:**
   * Formulate the fix hypothesis.
   * Patch only the offending attributes in `config.yaml` or Terraform wrappers.
   * Avoid full rewrites; preserve existing verified configuration.

4. **Re-Execute Loop Until Green:**
   * Re-run `uv run scripts/tdd_orchestrator.py --config <path-to-config.yaml> --infra-dir <path-to-infra-module>`.
   * Repeat autonomously until `🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED]` is emitted.
