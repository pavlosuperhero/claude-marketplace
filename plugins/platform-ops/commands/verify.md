---
description: Run the full 3-layer TDD verification (Layer 1 Static Analysis & fmt, Layer 2 Contract Tests, Layer 3 Plan Verification)
---

Execute the full 3-Layer TDD IaC Verification across this repository:

1. Locate the deployment configuration file in `deploy/**/config.yaml`.
2. Run the platform-ops TDD orchestrator via Bash:
   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/tdd_orchestrator.py" --config <path-to-config.yaml>
   ```
3. If Layer 1 (Schema / Format / Validate), Layer 2 (Contract Tests), or Layer 3 (Plan Verification) emit any RED failures, diagnose the root cause, patch the offending properties, and re-run until all 3 layers report GREEN.
