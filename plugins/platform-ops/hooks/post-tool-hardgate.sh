#!/usr/bin/env bash
# PostToolUse Hook: Fires after Write or Edit tool completes
set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
INPUT=$(cat || true)

# Extract file path from env var or stdin JSON
FILE_PATH="${CLAUDE_TOOL_INPUT_FILE_PATH:-}"
if [ -z "$FILE_PATH" ] && [ -n "$INPUT" ]; then
  FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | cut -d'"' -f4 || true)
fi

# Check if target is a deployment manifest
if [[ "$FILE_PATH" == *"deploy/"* ]]; then
  echo ""
  echo "══════════════════════════════════════════════════════════════════════"
  echo "🚨 [PLATFORM-OPS HARDGATE]: Deployment asset modified: $FILE_PATH"
  echo "══════════════════════════════════════════════════════════════════════"
  echo "⚠️ MANDATORY INSTRUCTION FOR CLAUDE:"
  echo "Do NOT conclude or summarize after modifying deployment files."
  echo "You MUST now execute the TDD orchestrator using your Bash tool:"
  echo ""
  echo "  uv run \"${PLUGIN_ROOT}/scripts/tdd_orchestrator.py\" --config \"$FILE_PATH\""
  echo ""
  echo "Read any diagnostics, self-heal, and repeat until green."
  echo "══════════════════════════════════════════════════════════════════════"
  echo ""
fi

exit 0
