---
name: platform-ops
description: Spec-Driven Development (SDD) and Test-Driven Development (TDD) engine for onboarding, templating, and deploying containerized Node.js microservices and cloud infrastructure environments on AWS ECS using central ECR artifactory, declarative contracts, JSON Schemas, and Terraform contract tests.
---

# Platform Operations Skill

This skill automates and governs the lifecycle of microservices and cloud infrastructure environments using **Spec-Driven Development (SDD)** and **Test-Driven Development (TDD)**.

---

## 0. Supported Stack & Architecture Constraints

> [!NOTE]
> **Currently Supported Stack:**
> * **Application Runtime:** **Node.js** projects (NestJS, Express, React/Nginx SSR) running inside **AWS ECS Fargate & Fargate Spot**.
> * **Build Artifactory:** Centralized **Amazon ECR** repositories (`<account-id>.dkr.ecr.<region>.amazonaws.com/<service>`) for release images and builder cache images (`zippo-build:*`).
> * **Ingress & Traffic:** AWS Application Load Balancer (ALB) with path-based HTTPS routing and target group health probes.
> * **Secrets & Configuration:** AWS Systems Manager (SSM) Parameter Store (plain and SecureString) and AWS Secrets Manager.
> * **CI/CD:** Ephemeral AWS CodeBuild runners integrated via GitHub Actions `WORKFLOW_JOB_QUEUED` webhooks.

---

## 1. Core Documentation Map (Theme Pointers)

Before performing actions, refer to the authoritative specification documents:

* **Platform Architecture & Topology:** [01-architecture-overview.md](docs/01-architecture-overview.md)
* **Lifecycle vs. Application Boundaries:** [02-lifecycle-vs-app-roles.md](docs/02-lifecycle-vs-app-roles.md)
* **Continuous Deployment Workflow:** [03-deployment-process.md](docs/03-deployment-process.md)
* **Client Onboarding & Intake Questionnaire:** [04-client-onboarding-guide.md](docs/04-client-onboarding-guide.md)
* **Environment Provisioning Guide:** [05-environment-guide.md](docs/05-environment-guide.md)
* **Spec-Driven Methodology:** [06-spec-driven-development.md](docs/06-spec-driven-development.md)
* **Test-Driven Infrastructure & Contracts:** [07-test-driven-development.md](docs/07-test-driven-development.md)
* **JSON Schema Definitions:** [app-config.schema.json](schemas/app-config.schema.json) | [service-spec.schema.json](schemas/service-spec.schema.json) | [environment.schema.json](schemas/environment.schema.json)

---

## 2. Standard Workflows

### Workflow A: Onboard a New Application Service
When a user asks to deploy or onboard a new application or microservice:

1. **Intake Phase:**
   Prompt the user for the mandatory intake answers defined in [04-client-onboarding-guide.md](docs/04-client-onboarding-guide.md):
   * Service identifier (`<service-name>`, kebab-case)
   * Container listening port (e.g. `3000`, `8080`) & health check path (e.g. `/healthz`)
   * Ingress path patterns (e.g. `["/api/<service>/*"]`) & ALB rule priority
   * Task sizing (CPU units, memory in MiB, desired replica count)
   * Sidecars (e.g. redis, cache, log agent), SES/S3 permissions, SSM parameters, and secrets.

2. **Generate Specification Contract:**
   * Create `deploy/<env>/config.yaml` using the template at `templates/app/config.yaml.tpl`.

3. **Validate Against JSON Schema:**
   * Run the validator script:
     ```bash
     python3 tests/validate_configs.py <target-repo>/deploy/<env>/config.yaml
     ```
   * Enforce schema compliance before generating or applying Terraform code.

4. **Scaffold Deployment Manifests:**
   * Generate `deploy/<env>/main.tf` from `templates/app/main.tf.tpl`.
   * Generate `locals.tf`, `providers.tf`, `variables.tf`, and `versions.tf`.
   * Generate CI/CD workflow from `templates/app/ci-workflow.yml.tpl`.

5. **Run Contract Tests (TDD):**
   * Execute the Terraform contract test suite:
     ```bash
     terraform -chdir=tests/tftests test -filter=app_contract.tftest.hcl
     ```
   * Verify all assertions pass before merging or applying.

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
   * Run `validate_configs.py` across all created manifests.

---

### Workflow C: Add a New Secret or Environment Variable
Follow the dynamic provisioning pattern in [03-deployment-process.md](docs/03-deployment-process.md):
1. Add the variable or secret entry to `config.yaml` (`ENV_VARS` or `SECRETS`).
2. Run `python3 tests/validate_configs.py <path-to-config.yaml>`.
3. Provision the resource via the automated CI workflow dispatch.
