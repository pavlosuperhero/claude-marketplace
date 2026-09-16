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
   * The primary spec source is **Confluence via MCP** (when available) or an explicitly configured `--specs-dir <path>` / `ADDITIONAL_SPECS_PATH` env var. Local directory auto-discovery (`Project_Specifications/`, `zippo-specs/`) is a convenience fallback — the tool probes those names as a hint if nothing else is configured.
   * If a specs directory is available from any of the above sources, scan it for context. Look for:
     - **Networking/ingress docs** — any existing ALB rule priorities and path patterns. Treat these as hints only, **not the source of truth**; a static doc drifts from what is actually deployed. The authoritative answer comes from the live sibling configs via `tests/check_ingress_collisions.py`.
     - **Sizing/deployment docs** — CPU/memory baselines, desired replica counts, subnet guidance.
     - **IAM/security docs** — permission boundary requirements (e.g. `eo_role_boundary`), allowed permission scopes.
   * Auto-fill known parameters from discovered context and only prompt the user for unique application-specific parameters — **except `ALB.path_patterns` and `ALB.priority`, which are never auto-filled.** See Step 2.

2. **Intake & Escalation Check:**
   Prompt the user for the remaining intake answers in [04-client-onboarding-guide.md](docs/04-client-onboarding-guide.md):
   * Service identifier (`<service-name>`, kebab-case)
   * Container listening port (e.g. `3000`, `8080`) & health check path (e.g. `/healthz`)
   * Ingress path patterns (e.g. `["/api/<service>/*"]`) & unique ALB rule priority — **always ask explicitly; never infer, never copy from the template or a neighbouring service.** Then verify the answer against the live configs before generating anything:
     ```bash
     uv run tests/check_ingress_collisions.py --config <path-to-config.yaml>
     ```
     Catching this at intake costs one question. Catching it at `terraform apply` costs an outage.
   * Task sizing (CPU units, memory in MiB, desired replica count)
   * Sidecars (e.g. redis cache), SES/S3 permissions, SSM parameters, and secrets.
   * **🚨 ESCALATION TRIGGERS:** If the service requires non-default subnets, dedicated security group ingress CIDRs, dedicated direct ALB ports, or IAM permissions beyond SES/S3/SSM/Secrets (e.g., DynamoDB, SQS), pause self-service generation and output an **Escalation Request** for the Platform Team.
   * **🚨 ESCALATION TRIGGERS (ingress):** Also pause and escalate if the service would claim a **catch-all** (`/*`), take a `path_patterns` or `priority` already held by another service, or sit behind an existing catch-all at a lower priority number. Each of these decides which service receives traffic. See *Ingress ownership is never yours to decide* below.

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

2. **Honour the exit-code contract.** It decides whether you may act autonomously:

   | Exit | Verdict | Your action |
   |------|---------|-------------|
   | `0` + `🟢 GREEN` | every layer verified | Proceed. |
   | `0` + `🟡 PARTIAL` | tests passed, some layer **did not run** | **Do not call this verified.** Report verbatim which layers did not run and why. |
   | `1` + `🔴 RED` | a real defect | Self-heal per Step 4, then re-run. |
   | `2` + `🟣 ESCALATION` | conflict only a human can resolve | **STOP. Do not edit any file.** Relay the options and wait. |

3. **Never convert a 🟡 PARTIAL into a claim of success.** `terraform plan` (Layer 3) and `terraform validate` require `terraform init` plus valid AWS credentials. When those are absent the orchestrator prints a `DIAGNOSTIC:` block with `failure_class` and `disposition: BLOCKED`, and the summary lists the layer under **NOT verified**. Say so explicitly — "Layer 3 did not run: blocked by NOT_INITIALIZED" — rather than reporting the run as complete. A layer that was skipped proved nothing.

4. **Diagnose Failures (Red State):**
   * Read the `DIAGNOSTIC:` block first. Its `failure_class` and `remediation` fields are authoritative; do not re-derive a theory from raw output when a class is already named.
   * If `disposition: BLOCKED`, the problem is the **environment**, not the code. Fix that (`terraform init`, credentials) and re-run. Do **not** edit manifests — zero assertions ran, so nothing has been shown wrong.
   * If **Schema Violation:** Inspect reported missing properties, disallowed port ranges, or malformed SSM paths against `schemas/app-config.schema.json`.
   * If **Terraform Assertion Failure:** Read the failed assertion from the `*.tftest.hcl` in the module under test (e.g. missing health check path, or ungranted S3/SES permissions).

5. **Apply Surgical Patch:**
   * Formulate the fix hypothesis.
   * Patch only the offending attributes in `config.yaml` or Terraform wrappers.
   * Avoid full rewrites; preserve existing verified configuration.

6. **Re-Execute Loop Until Green:**
   * Re-run `uv run scripts/tdd_orchestrator.py --config <path-to-config.yaml> --infra-dir <path-to-infra-module>`.
   * Repeat autonomously until `🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED]` is emitted — **unless** the run exited `2` (escalation) or ended `🟡 PARTIAL`. Those two states are terminal for autonomous work: report and stop.

---

### Ingress ownership is never yours to decide

`ALB.priority` and `path_patterns` must be unique across every service sharing the ALB. The JSON Schema cannot enforce this — it sees one file at a time — so the orchestrator runs a cross-service check in Layer 1:

```bash
uv run tests/check_ingress_collisions.py --config <path-to-config.yaml>
```

Exit `2` means a **HARD** collision: duplicate priority (AWS rejects the apply with `PriorityInUse`), a duplicate path pattern, or a catch-all shadowing this service.

**Reassigning a path pattern or priority decides which service receives production traffic, and for a catch-all it decides which service goes dark. That is a product decision, not a formatting fix.** When the checker escalates:

1. **First, check whether the two are even different applications.** The checker compares config files; it cannot see that two directories are the same codebase. Before relaying options, compare the colliding repos:
   ```bash
   git -C <repo-a> remote get-url origin; git -C <repo-b> remote get-url origin
   git -C <repo-a> rev-parse HEAD;         git -C <repo-b> rev-parse HEAD
   ```
   Same remote or same HEAD means this is **one application about to be deployed twice** — a rename, a migration, or a stray working copy. Coexist-vs-replace is then the wrong question; ask why it is deployed twice and which name is intended to survive. Say plainly that the two are identical rather than presenting them as peer services.
2. Relay the checker's enumerated options (coexist / replace / invert / defer) to the human verbatim.
3. State the blast radius of each — which URLs break, which target group stops receiving traffic.
4. Stop. Resume only after the human states a choice explicitly.

Never pick a free priority to make the pipeline go green. A green pipeline that silently displaced a live service is a worse outcome than a blocked one. New service configs are frequently copied from an existing service, so an inherited `/*` at the same priority is a template artifact — treat it as unspecified intent, not as an expressed decision.
