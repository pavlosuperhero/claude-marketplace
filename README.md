# claude-marketplace

A curated collection of production-grade skills, templates, and plugins for **Claude Code** and AI coding assistants.

---

## Available Plugins & Skills

| Plugin / Skill | Description | Location |
| :--- | :--- | :--- |
| **`platform-ops`** | Spec-Driven Development (SDD) & Test-Driven Development (TDD) engine for containerized microservices and cloud infrastructure. | [`skills/platform-ops`](skills/platform-ops) |

---

## Installation Guide for Claude Code

You can install and use the `platform-ops` skill in Claude Code using any of the methods below.

### Method 1: Add Marketplace via Claude Code CLI (Recommended)

1. **Add the Marketplace:**
   ```bash
   claude plugin marketplace add Learning-and-templating/claude-marketplace
   ```
   *Or using SSH git URL:*
   ```bash
   claude plugin marketplace add git@github.com:Learning-and-templating/claude-marketplace.git
   ```

2. **Install the `platform-ops` Plugin:**
   ```bash
   claude plugin install platform-ops@claude-marketplace
   ```

3. **Verify Installation:**
   ```bash
   claude plugin list
   ```

---

### Method 2: Configure in `~/.claude/` Manually

If you prefer configuring your global Claude Code settings manually:

1. **Register the Marketplace:**
   Open `~/.claude/plugins/known_marketplaces.json` and add `claude-marketplace`:
   ```json
   {
     "claude-plugins-official": {
       "source": {
         "source": "github",
         "repo": "anthropics/claude-plugins-official"
       },
       "installLocation": "/Users/<your-user>/.claude/plugins/marketplaces/claude-plugins-official",
       "lastUpdated": "2026-08-25T13:06:35.765Z"
     },
     "claude-marketplace": {
       "source": {
         "source": "github",
         "repo": "Learning-and-templating/claude-marketplace"
       },
       "installLocation": "/path/to/claude-marketplace",
       "lastUpdated": "2026-09-15T12:00:00.000Z"
     }
   }
   ```

2. **Enable in `~/.claude/settings.json`:**
   ```json
   {
     "enabledPlugins": {
       "platform-ops@claude-marketplace": true
     }
   }
   ```

---

### Method 3: Direct Project / Workspace Installation

To use `platform-ops` as a project-level skill without global marketplace installation:

```bash
# From within your project root:
mkdir -p .claude/skills
cp -r /path/to/claude-marketplace/skills/platform-ops .claude/skills/
```

Claude Code will automatically detect `.claude/skills/platform-ops/SKILL.md` for your project workspace.

---

## How to Use `platform-ops`

Once installed, Claude Code can autonomously execute end-to-end platform workflows:

### 1. Onboarding a New Microservice (Spec-Driven)
Simply prompt Claude Code:
> *"I want to onboard and deploy a new microservice named `order-service` on port 8080 with Redis cache."*

The skill will:
1. Conduct the 8-question intake interview.
2. Generate the declarative `deploy/<env>/config.yaml`.
3. Validate the manifest against `schemas/app-config.schema.json`.
4. Scaffold Terraform deployment wrappers (`main.tf`, `locals.tf`, `versions.tf`) and GitHub Actions CI workflow.
5. Execute Terraform contract tests (`*.tftest.hcl`) with mock AWS providers.

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
│   └── marketplace.json                  # Official marketplace registry catalog
├── skills/
│   └── platform-ops/                     # The platform-ops skill & plugin
│       ├── .claude-plugin/
│       │   └── plugin.json               # Plugin metadata
│       ├── SKILL.md                      # Claude Code skill definition (< 500 lines)
│       ├── docs/                         # In-depth architectural & operational guides
│       ├── schemas/                      # JSON Schemas for configs and environments
│       ├── templates/                    # Jinja/HCL/YAML templates for apps and envs
│       ├── tests/                        # Native Terraform tests & schema validators
│       └── prompts/                      # Ready-to-use LLM scaffolding prompts
├── marketplace.json                      # Root marketplace manifest
└── README.md                             # Marketplace documentation & install guide
```
