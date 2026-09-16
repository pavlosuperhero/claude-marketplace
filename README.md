# claude-marketplace

A curated collection of production-grade plugins, skills, and templates for **Claude Code** and AI coding assistants.

---

## Available Plugins & Skills

| Plugin / Skill | Description | Location |
| :--- | :--- | :--- |
| **`platform-ops`** | Spec-Driven Development (SDD) & Test-Driven Development (TDD) engine for containerized microservices and cloud infrastructure. | [`plugins/platform-ops`](plugins/platform-ops) |

> **Currently Supported Stack:** **Node.js** projects running inside **AWS ECS (Fargate & Fargate Spot)** with a centralized **Amazon ECR** build artifactory.

---

## Installation Guide for Claude Code

Install and use the `platform-ops` plugin directly from this GitHub marketplace:

### Step 1: Add Marketplace to Claude Code

Run the Claude Code CLI command:
```bash
claude plugin marketplace add pavlosuperhero/claude-marketplace
```

*Or using the Git HTTPS URL:*
```bash
claude plugin marketplace add https://github.com/pavlosuperhero/claude-marketplace.git
```

*Or using SSH:*
```bash
claude plugin marketplace add git@github.com:pavlosuperhero/claude-marketplace.git
```

---

### Step 2: Install the `platform-ops` Plugin

```bash
claude plugin install platform-ops@pavlo-marketplace
```

---

### Step 3: Verify Installation

Check that the plugin is installed and active:
```bash
claude plugin list
```

---

## How to Use `platform-ops`

Once installed, Claude Code can autonomously execute end-to-end platform workflows:

### 1. Onboarding a New Microservice (Spec-Driven)
Prompt Claude Code:
> *"I want to onboard and deploy a new microservice named `order-service` on port 8080 with Redis cache."*

The skill will:
1. Conduct the intake interview (including Predefined Baseline & Escalation checks).
2. Generate the declarative `deploy/<env>/config.yaml`.
3. Validate the manifest with `uv run tests/validate_configs.py --config <file>`.
4. Scaffold Terraform deployment wrappers (`main.tf`, `locals.tf`, `versions.tf`) and CI workflow.
5. Execute the visual TDD Orchestrator:
   ```bash
   uv run scripts/tdd_orchestrator.py --config deploy/dev/config.yaml --infra-dir /path/to/infra/module
   ```
6. Self-heal any schema or assertion failures autonomously until `🟢 [GREEN]`.


### 2. Adding a New Infrastructure Environment
> *"Scaffold a new `stage` environment for our platform."*

The skill will:
1. Scaffold `lifecycle/stage/main.tf` and `terraform.tfvars`.
2. Validate against `schemas/environment.schema.json`.
3. Run environment contract tests.
4. Replicate and validate service manifests across all microservices.

---

## Repository Structure

```
claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json                  # Official marketplace registry catalog (git-subdir sources)
├── marketplace.json                      # Root marketplace manifest
├── plugins/
│   └── platform-ops/                     # The platform-ops plugin
│       ├── .claude-plugin/
│       │   └── plugin.json               # Plugin metadata
│       ├── SKILL.md                     # Plugin-level index (routes to skills, prompts, commands)
│       ├── skills/
│       │   └── platform-ops/
│       │       └── SKILL.md              # Full SDD/TDD skill instructions
│       ├── docs/                         # In-depth architectural & operational guides
│       ├── schemas/                      # JSON Schemas for configs and environments
│       ├── templates/                    # Jinja/HCL/YAML templates for apps and envs
│       ├── tests/                        # Native Terraform tests & schema validators
│       └── prompts/                      # Ready-to-use LLM scaffolding prompts
└── README.md                             # Marketplace documentation & install guide
```
