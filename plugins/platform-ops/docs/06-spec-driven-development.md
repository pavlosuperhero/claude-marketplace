# 06. Spec-Driven Development (SDD) Workflow

Spec-Driven Development (SDD) is the operational paradigm used in ZIPPO to ensure all infrastructure, application deployments, and CI/CD pipelines are generated from a single, deterministic contract rather than ad-hoc scripts or prompts.

---

## 1. Why Spec-Driven Development?

In cloud and AI-assisted development, manual prompting or free-form editing leads to:
* **Configuration Drift:** Missing health checks, incorrect ALB priorities, or improperly formatted SSM paths.
* **Security Regressions:** Missing permissions boundaries, insecure environment variables, or overly broad IAM policies.
* **Context Hallucinations:** AI assistants guessing non-existent parameters or altering critical production defaults.

By using SDD, the **Specification** is the contract. Code generation and deployment tools operate within strict boundaries defined by JSON Schemas.

---

## 2. The 4-Phase SDD Cycle

```
  ┌────────────────────────────────────────────────────────┐
  │ 1. SPECIFY (The Contract)                              │
  │    Complete the intake spec in deploy/<env>/config.yaml│
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │ 2. VALIDATE (Automated Gate)                           │
  │    Validate YAML against app-config.schema.json        │
  │    Reject invalid ports, missing fields, bad regex     │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │ 3. SCAFFOLD (Deterministic Generation)                 │
  │    Generate main.tf, locals.tf, versions.tf, and CI    │
  │    workflows strictly from verified templates          │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │ 4. APPLY & SYNCHRONIZE                                 │
  │    Terraform apply and CI execution commit changes.    │
  │    If requirements change, update the spec FIRST.      │
  └────────────────────────────────────────────────────────┘
```

---

## 3. Schema Governance

* The schema definition is stored in `schemas/app-config.schema.json`.
* Validation is executed locally or in CI via:
  ```bash
  uv run tests/validate_configs.py <path-to-config.yaml>
  ```
* No Terraform code may be planned or applied if schema validation fails.
