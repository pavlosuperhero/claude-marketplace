# Platform Operations (`platform-ops`)

An autonomous, production-grade **Spec-Driven Development (SDD)** and **Test-Driven Development (TDD)** engine for onboarding, templating, and deploying containerized microservices to AWS ECS Fargate.

---

## Supported Stack & Architecture Constraints

> **Currently Supported Stack:**
> * **Runtime:** **Node.js** projects (e.g., NestJS, Express, React/Node SSR) running as containerized tasks inside **AWS ECS (Fargate & Fargate Spot)**.
> * **Artifact Management:** Centralized **Amazon ECR (Elastic Container Registry)** serving as the build artifactory for service images (`<account-id>.dkr.ecr.<region>.amazonaws.com/<service>`) and shared base runner images (`zippo-build:*`).
> * **Ingress:** AWS Application Load Balancer (ALB) with path-based HTTPS routing and target group health checking.
> * **Configuration & Secrets:** AWS Systems Manager (SSM) Parameter Store (plain and KMS SecureString) and AWS Secrets Manager.
> * **CI/CD:** Ephemeral AWS CodeBuild runners integrated directly with GitHub Actions via `WORKFLOW_JOB_QUEUED` webhooks.

---

## Key Features

1. **Spec-Driven Development (SDD):**
   * Single source of truth per environment (`deploy/<env>/config.yaml`).
   * Strict schema validation via JSON Schema (`schemas/app-config.schema.json`).
   * Eliminates configuration drift and prevents invalid parameters before any cloud provisioning.

2. **Test-Driven Development (TDD):**
   * Native Terraform test suites (`*.tftest.hcl`) with mocked AWS providers.
   * Instant local and CI plan-level contract assertion checks in < 3 seconds with zero AWS costs.

3. **Autonomous Turnkey Scaffolding:**
   * Generates production-ready Terraform modules calling `aws-epam-ecs-app`.
   * Provisions scoped IAM task roles (SES email, S3 bucket access, SSM/SecretsManager read).
   * Generates ready-to-run GitHub Actions CI/CD workflows.

---

## Directory Structure

```
platform-ops/
├── .claude-plugin/
│   └── plugin.json                       # Claude Code plugin manifest
├── skills/
│   └── platform-ops/
│       └── SKILL.md                      # Claude Code skill definition (< 500 lines)
├── docs/
│   ├── 01-architecture-overview.md       # Topology and traffic flow
│   ├── 02-lifecycle-vs-app-roles.md      # Platform vs. Application boundary matrix
│   ├── 03-deployment-process.md          # CI/CD, SSM image tagging, TF apply
│   ├── 04-client-onboarding-guide.md     # 8-question intake interview
│   ├── 05-environment-guide.md           # Multi-environment provisioning
│   ├── 06-spec-driven-development.md     # SDD governance & rules
│   └── 07-test-driven-development.md     # TDD red-green-refactor in IaC
├── schemas/
│   ├── app-config.schema.json            # JSON Schema for deploy/<env>/config.yaml
│   ├── service-spec.schema.json          # Master service onboarding schema
│   └── environment.schema.json           # Environment lifecycle schema
├── templates/
│   ├── app/                              # Microservice deployment templates
│   └── env/                              # Environment lifecycle templates
├── tests/
│   ├── tftests/                          # Native Terraform tests (app_contract, env_contract)
│   └── validate_configs.py               # Self-contained YAML schema validator
└── prompts/
    ├── scaffold-new-app.prompt.md        # Prompt for onboarding new microservices
    └── add-new-environment.prompt.md     # Prompt for creating new environments
```

---

## Usage in Claude Code

Prompt Claude Code to onboard any new Node.js microservice:
```
Onboard a new Node.js service named "zippo-certs" on port 3000, health check "/api/v1/certs/health", ALB path "/api/v1/certs/*" with priority 5, using central ECR artifactory.
```
