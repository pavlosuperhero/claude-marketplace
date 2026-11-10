---
description: Run the full 3-layer TDD verification (Layer 1 Static Analysis & fmt, Layer 2 Contract Tests, Layer 3 Plan Verification)
---

Execute the full 3-Layer TDD IaC Verification across this repository:

1. Locate the deployment configuration file in `deploy/**/config.yaml`.
2. Use the module directory from `INFRA_REPO_PATH`, or pass its path via `--infra-dir`. The runner looks for `app_contract.tftest.hcl` under `tests/` or the module root. Pass `--contract-test` for another suite. Run the orchestrator via Bash:
   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/tdd_orchestrator.py" --config "<path-to-config.yaml>" --infra-dir "<path-to-app-module>"
   ```
3. Report which layers ran. On RED, fix the diagnosed contract failure and re-run. On PARTIAL or BLOCKED, report the missing verification and its cause. On exit 2, relay the ingress decision to the user and wait.
