#!/usr/bin/env bash
# Stop Hook: Hardgate that blocks Claude from finishing if deployment configs are invalid or unverified
set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
INPUT=$(cat || true)

# 1. Prevent infinite recursion loop if stop hook is already active
if echo "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

# 2. Determine the project root (prefer CLAUDE_PROJECT_ROOT, fall back to CWD)
PROJECT_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"

# 3. Check if any deploy/ config.yaml exists in the project
CONFIG_FILE=$(find "$PROJECT_ROOT" -maxdepth 4 -path "*/deploy/*/config.yaml" 2>/dev/null | head -n 1 || true)

if [ -z "$CONFIG_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
  # No deployment configuration present in this repo, allow stop
  exit 0
fi

# 4. Check if the config passes schema validation
VALIDATOR="${PLUGIN_ROOT}/tests/validate_configs.py"
if [ -f "$VALIDATOR" ]; then
  VAL_OUTPUT=$(uv run "$VALIDATOR" --config "$CONFIG_FILE" 2>&1 || true)
  
  if echo "$VAL_OUTPUT" | grep -q "VALIDATION FAILURES DETECTED\|FAILED:"; then
    echo "❌ [HARDGATE BLOCKED]: Cannot stop! Deployment configuration '$CONFIG_FILE' violates specification schema:" >&2
    echo "$VAL_OUTPUT" >&2
    echo "" >&2
    echo "👉 ACTION REQUIRED: Fix the schema violations above, then execute the TDD orchestrator:" >&2
    echo "   uv run \"${PLUGIN_ROOT}/scripts/tdd_orchestrator.py\" --config \"$CONFIG_FILE\"" >&2
    exit 2
  fi
fi

# 5. Check if Terraform files exist and are formatted
DEPLOY_DIR=$(dirname "$CONFIG_FILE")
if [ -d "$DEPLOY_DIR" ] && compgen -G "$DEPLOY_DIR/*.tf" > /dev/null; then
  if ! TF_CLI_CONFIG_FILE=/dev/null terraform -chdir="$DEPLOY_DIR" fmt -check >/dev/null 2>&1; then
    echo "❌ [HARDGATE BLOCKED]: Terraform files in '$DEPLOY_DIR' fail canonical style formatting!" >&2
    echo "👉 ACTION REQUIRED: Run 'terraform fmt' in '$DEPLOY_DIR' before concluding." >&2
    exit 2
  fi
fi

exit 0
