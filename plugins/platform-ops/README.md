# Platform Operations (`platform-ops`)

An autonomous, production-grade **Spec-Driven Development (SDD)** and **Test-Driven Development (TDD)** engine for onboarding, templating, and deploying containerized microservices to AWS ECS Fargate.

---

## Supported Stack & Architecture Constraints

> **Currently Supported Stack:**
> * **Runtime:** **Node.js** projects (e.g., NestJS, Express, React/Node SSR) running as containerized tasks inside **AWS ECS (Fargate & Fargate Spot)**.
> * **Artifact Management:** Centralized **Amazon ECR (Elastic Container Registry)** serving as the build artifactory for service images (`<account-id>.dkr.ecr.<region>.amazonaws.com/<service>`) and shared builder cache images (`<project>-build:*`).
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
   * Generates Terraform wrappers for your application and environment modules.
   * Provisions scoped IAM task roles (SES email, S3 bucket access, SSM/SecretsManager read).
   * Generates ready-to-run GitHub Actions CI/CD workflows.

---

## Directory Structure

```
platform-ops/
├── .claude-plugin/
│   └── plugin.json                       # Claude Code plugin manifest
├── SKILL.md                              # Plugin overview
├── skills/
│   └── platform-ops/
│       └── SKILL.md                      # Skill loaded by Claude Code
├── hooks/
│   ├── hooks.json                        # Hook definitions (PostToolUse, Stop)
│   ├── post-tool-hardgate.sh             # Requests a TDD run after deploy/ file edits
│   ├── pre-tool-guard.sh                 # PreToolUse safety checks
│   └── stop-hardgate.sh                  # Blocks session stop until schema + fmt pass (exits 2 on failure)
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
├── scripts/
│   ├── tdd_orchestrator.py               # 3-layer TDD runner (schema → contract tests → plan)
│   └── platform_ops_paths.py             # Shared plugin and local-spec paths
├── templates/
│   ├── app/                              # Microservice deployment templates
│   └── env/                              # Environment lifecycle templates
├── tests/
│   ├── tftests/                          # Native Terraform tests (app_contract, env_contract)
│   ├── validate_configs.py               # Self-contained YAML schema validator
│   └── check_ingress_collisions.py       # Cross-service ALB priority collision checker
└── prompts/
    ├── scaffold-new-app.prompt.md        # Prompt for onboarding new microservices
    └── add-new-environment.prompt.md     # Prompt for creating new environments
```

---

## Usage in Claude Code

Load a local checkout with `claude --plugin-dir /absolute/path/to/plugins/platform-ops` from your service repository. Use `/platform-ops:verify` to run the checks. The bundled scripts resolve relative to the installed plugin, and deployment paths resolve from your working directory.

If you host Claude Code through the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/plugins), pass `plugins=[{"type": "local", "path": "/absolute/path/to/plugins/platform-ops"}]` to `ClaudeAgentOptions` and set `cwd` to the service repository. The SDK loads the same plugin components.

Prompt Claude Code to onboard any new Node.js microservice:
```
Onboard a new Node.js service named "cert-service" on port 3000, health check "/api/v1/certs/health", ALB path "/api/v1/certs/*" with priority 5, using central ECR artifactory.
```

## Configuration

Set these environment variables in the shell that launches Claude Code or pass the corresponding flags when running a script. Flags take precedence over the environment.

| CLI flag | Environment variable | Value |
| --- | --- | --- |
| `--infra-dir` | `INFRA_REPO_PATH` | Directory with the Terraform configuration and runnable contract tests. Required for the orchestrator. |
| `--contract-test` | `CONTRACT_TEST_PATH` | Terraform test file relative to the module. Defaults to `tests/app_contract.tftest.hcl`, then `app_contract.tftest.hcl` at the module root. |
| `--config` | `APP_CONFIG_PATH` | Deployment YAML path for the orchestrator, ingress checker, and Stop hook. |
| `--schema` | `APP_SCHEMA_PATH` | Optional app schema override, also used by the Stop hook. |
| `--specs-dir` | `ADDITIONAL_SPECS_PATH` or `PROJECT_SPECS_PATH` | Optional local spec directory. Otherwise both tools look for `Project_Specifications` in the current directory and up to three ancestors. |
| `--workspace-root` | `WORKSPACE_ROOT` | Parent of sibling service repos for ingress checks. |

Run the orchestrator with `--strict` in CI. An incomplete run reports `PARTIAL` and exits `3` in strict mode. Interactive runs preserve exit `0` for `PARTIAL`. For ALB-backed services, missing or unreadable peers make ingress verification incomplete. Select a trusted contract suite with mock providers because Terraform can execute `apply` steps defined in a test file.

Run the orchestrator's regression tests with `python3 -m unittest discover -s tests` from the plugin directory.

When scaffolding from a template, resolve these placeholders from the target project before generating files.

| Scope | Template inputs |
| --- | --- |
| Project and AWS | `PROJECT_NAME`, `ENVIRONMENT`, `AWS_REGION` |
| Terraform | `APP_MODULE_SOURCE`, `ENV_MODULE_SOURCE`, `STATE_BUCKET`, `STATE_KEY`, `STATE_REGION` |
| ECR and CI | `ECR_REPOSITORIES` (comma-separated quoted names), `BUILDER_ECR_REPOSITORY`, `RUNNER_PROJECT_NAME`, `RUNNER_TAG_SSM_PATH`, `INFRA_REPOSITORY_URL` |

Use the existing bucket, key, and region when regenerating manifests for an existing deployment. Terraform uses those values to locate its state.

The deployment specification PDF can be regenerated with `python3 tests/generate_pdf.py` from the plugin directory. Use `--title` and `--output` for a project-specific copy.
