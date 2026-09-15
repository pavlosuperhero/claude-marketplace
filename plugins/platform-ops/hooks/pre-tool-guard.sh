#!/usr/bin/env bash
# PreToolUse Hook: Guards against destructive operations on deployment infrastructure
set -e

INPUT=$(cat || true)

# Extract the command being executed from stdin JSON or environment
COMMAND_LINE="${CLAUDE_TOOL_INPUT_COMMAND:-}"
if [ -z "$COMMAND_LINE" ] && [ -n "$INPUT" ]; then
  COMMAND_LINE=$(echo "$INPUT" | grep -oE '"(command|CommandLine)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | cut -d'"' -f4 || true)
fi

# Block destructive Terraform commands without explicit user approval context
if echo "$COMMAND_LINE" | grep -qiE 'terraform\s+(destroy|apply.*-auto-approve|import|state\s+(rm|mv|push))'; then
  echo ""
  echo "══════════════════════════════════════════════════════════════════════"
  echo "⚠️  [PLATFORM-OPS GUARD]: Destructive Terraform command detected!"
  echo "══════════════════════════════════════════════════════════════════════"
  echo "Command: $COMMAND_LINE"
  echo ""
  echo "This command modifies live infrastructure. Before proceeding:"
  echo "  1. Ensure all TDD contract tests are GREEN"
  echo "  2. Review the terraform plan output"
  echo "  3. Confirm the target environment is correct"
  echo "══════════════════════════════════════════════════════════════════════"
  echo ""
fi

# Block accidental deletion of deployment configs
if echo "$COMMAND_LINE" | grep -qiE '(rm|del|remove).*deploy/'; then
  echo ""
  echo "══════════════════════════════════════════════════════════════════════"
  echo "🚨 [PLATFORM-OPS GUARD]: Deployment file deletion detected!"
  echo "══════════════════════════════════════════════════════════════════════"
  echo "Command: $COMMAND_LINE"
  echo "Deleting deployment configurations is destructive. Proceed with caution."
  echo "══════════════════════════════════════════════════════════════════════"
  echo ""
fi

exit 0
