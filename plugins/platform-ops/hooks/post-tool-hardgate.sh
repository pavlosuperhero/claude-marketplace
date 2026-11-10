#!/usr/bin/env bash
# PostToolUse Hook: Fires after Write or Edit tool completes
set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
INPUT=$(cat || true)

# Extract file path from env var or stdin JSON (try multiple key names)
FILE_PATH="${CLAUDE_TOOL_INPUT_FILE_PATH:-}"
if [ -z "$FILE_PATH" ] && [ -n "$INPUT" ]; then
  if command -v jq >/dev/null 2>&1; then
    FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input | .file_path // .TargetFile // .path // .target_file // empty' 2>/dev/null || true)
  else
    FILE_PATH=$(echo "$INPUT" | grep -oE '"(TargetFile|file_path|path|target_file)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | cut -d'"' -f4 || true)
  fi
fi
# Fallback: check tool output for written file path
if [ -z "$FILE_PATH" ]; then
  FILE_PATH="${CLAUDE_TOOL_OUTPUT_FILE_PATH:-}"
fi

# Use the sibling YAML contract when a Terraform file was edited.
case "/$FILE_PATH" in
  */deploy/*/*)
  CONFIG_PATH="$(dirname "$FILE_PATH")/config.yaml"
  VERIFY_COMMAND=$(printf 'uv run %q --config %q' "$PLUGIN_ROOT/scripts/tdd_orchestrator.py" "$CONFIG_PATH")
  if [ -n "${INFRA_REPO_PATH:-}" ]; then
    VERIFY_COMMAND+=$(printf ' --infra-dir %q' "$INFRA_REPO_PATH")
  fi
  ;;
  *) exit 0 ;;
esac

MESSAGE=$(
  echo ""
  echo "══════════════════════════════════════════════════════════════════════"
  echo "🚨 [PLATFORM-OPS HARDGATE]: Deployment asset modified: $FILE_PATH"
  echo "══════════════════════════════════════════════════════════════════════"
  echo "⚠️ MANDATORY INSTRUCTION FOR CLAUDE:"
  echo "Do NOT conclude or summarize after modifying deployment files."
  echo "You MUST now execute the TDD orchestrator using your Bash tool:"
  echo ""
  echo "  $VERIFY_COMMAND"
  echo "Set INFRA_REPO_PATH or pass --infra-dir with the module that contains the contract tests."
  echo ""
  echo "Read any diagnostics, self-heal, and repeat until green."
  echo "══════════════════════════════════════════════════════════════════════"
  echo ""
)

if command -v jq >/dev/null 2>&1; then
  jq -n --arg message "$MESSAGE" \
    '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $message}}'
else
  printf '%s\n' "$MESSAGE"
fi

exit 0
