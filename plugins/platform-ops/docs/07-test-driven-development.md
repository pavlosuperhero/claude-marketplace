# 07. Test-Driven Development (TDD) for Infrastructure

Test-Driven Development (TDD) for Infrastructure adapts the classic Red-Green-Refactor cycle to Cloud Architecture and Terraform using native test suites.

---

## 1. The Red-Green-Refactor Loop in Terraform

```
  ┌────────────────────────────────────────────────────────┐
  │ 1. RED: Write the Failing Contract Test                │
  │    Write assertions in *.tftest.hcl using mock AWS     │
  │    providers. Test fails because resource or rule is   │
  │    not yet defined.                                    │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │ 2. GREEN: Implement Minimum IaC / Config               │
  │    Update config.yaml or the Terraform module to       │
  │    satisfy the assertion. Test passes instantly.       │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │ 3. REFACTOR: Optimize & Harden                         │
  │    Refactor policies, remove redundancies, run fmt &   │
  │    validate. All contract tests remain green.          │
  └────────────────────────────────────────────────────────┘
```

---

## 2. Using the Native Terraform Test Framework

ZIPPO utilizes Terraform's native testing framework (`.tftest.hcl`), introducing fast, deterministic testing without provisioning real AWS infrastructure:

* **Mock Providers:** `mock_provider "aws"` mocks all API calls, preventing AWS credential dependencies and eliminating cloud costs.
* **Command Mode:** Running with `command = apply` or `command = plan` checks HCL logic, conditionals, dynamic blocks, and variable validation rules.
* **Instant Feedback:** Tests execute in under 3 seconds.

### Running Contract Tests:
```bash
# Run application contract test suite
terraform -chdir=ZIPPO-INFR/iac/aws-epam-ecs-app test

# Run environment contract test suite
terraform -chdir=ZIPPO-INFR/iac/aws-epam-ecs test
```

---

## 3. Test Layers & Gating in CI/CD

1. **Layer 1: Static Analysis** (`terraform fmt -check`, `terraform validate`, `validate_configs.py`).
2. **Layer 2: Contract Unit Tests** (`terraform test` with mock providers).
3. **Layer 3: Plan Verification** (`terraform plan`).
4. **Layer 4: Deployment Execution** (`terraform apply -auto-approve`).
