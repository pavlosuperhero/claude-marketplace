# claude-marketplace

A curated collection of production-grade skills and templates for Claude Code and AI coding assistants.

## Available Skills

| Skill | Description | Location |
| :--- | :--- | :--- |
| **`platform-ops`** | Spec-Driven Development (SDD) & Test-Driven Development (TDD) engine for containerized microservice deployments and cloud environments. | [`skills/platform-ops`](skills/platform-ops) |

---

## Skill: `platform-ops`

The `platform-ops` skill provides an end-to-end blueprint to onboard, validate, template, and deploy microservices to AWS ECS Fargate and manage multi-environment cloud infrastructure.

### Features
* **Spec-Driven Development (SDD):** Enforces JSON Schemas on all declarative `config.yaml` service manifests.
* **Test-Driven Development (TDD):** Fast native Terraform contract tests (`*.tftest.hcl`) with mock AWS providers.
* **Turnkey Scaffolding:** Production-ready templates for ECS Fargate, ALB ingress routing, IAM scoping, and GitHub Actions CI/CD.
* **Comprehensive Docs:** Architecture overviews, responsibility matrices, deployment workflows, and client intake guides.

### Usage in Claude Code
Point Claude Code to this skill directory or copy `skills/platform-ops` into your project's `.claude/skills/` folder:
```bash
cp -r skills/platform-ops /path/to/project/.claude/skills/
```
