---
name: platform-ops
description: Spec-Driven Development (SDD) and Test-Driven Development (TDD) engine for onboarding, templating, and deploying containerized Node.js microservices and cloud infrastructure environments on AWS ECS using central ECR artifactory, declarative contracts, JSON Schemas, and Terraform contract tests.
---

# Platform Operations Plugin

This plugin automates and governs the lifecycle of microservices and cloud infrastructure environments using **Spec-Driven Development (SDD)** and **Test-Driven Development (TDD)**.

---

## Available Skills

| Skill | Description | Entrypoint |
| :--- | :--- | :--- |
| **`platform-ops`** | Full SDD/TDD engine: onboard services, scaffold environments, validate contracts, and self-heal via the TDD orchestrator. | [`skills/platform-ops/SKILL.md`](skills/platform-ops/SKILL.md) |

---

## Available Prompts

| Prompt | Use When… |
| :--- | :--- |
| [`scaffold-new-app`](prompts/scaffold-new-app.prompt.md) | Onboarding a new microservice to the platform. |
| [`add-new-environment`](prompts/add-new-environment.prompt.md) | Provisioning a new deployment environment (`stage`, `prod`, `qa`, `preview`). |

---

## Slash Commands

| Command | Description |
| :--- | :--- |
| `/verify` | Run the full 3-layer TDD verification (Schema → Contract Tests → Plan). |
| `/plan` | Run Layer 3 only — `terraform plan` dry-run preview. |
| `/fmt` | Format all Terraform files to canonical style. |

---

## Safety Hooks

This plugin enforces guardrails automatically:

- **PreToolUse** — Warns before destructive Terraform commands (`destroy`, `apply -auto-approve`, `state rm`).
- **PostToolUse** — Forces TDD orchestrator execution after any `deploy/` file is modified.
- **Stop** — Blocks session completion if `config.yaml` fails schema validation or `terraform fmt -check`.

---

## Core Documentation

Refer to the authoritative specification documents in [`docs/`](docs/):

* [01-architecture-overview.md](docs/01-architecture-overview.md) — Platform Architecture & Topology
* [02-lifecycle-vs-app-roles.md](docs/02-lifecycle-vs-app-roles.md) — Lifecycle vs. Application Boundaries
* [03-deployment-process.md](docs/03-deployment-process.md) — Continuous Deployment Workflow
* [04-client-onboarding-guide.md](docs/04-client-onboarding-guide.md) — Client Onboarding & Escalation Protocol
* [05-environment-guide.md](docs/05-environment-guide.md) — Environment Provisioning Guide
* [06-spec-driven-development.md](docs/06-spec-driven-development.md) — Spec-Driven Methodology
* [07-test-driven-development.md](docs/07-test-driven-development.md) — Test-Driven Infrastructure & Contracts
