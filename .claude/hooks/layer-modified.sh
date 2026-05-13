#!/usr/bin/env bash
# Remind Claude to update workflow.md after any layers/*.py edit.
f=$(jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
case "$f" in
  */layers/*.py)
    printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Layer file modified. Update the project workflow.md before this session ends."}}\n'
    ;;
esac
