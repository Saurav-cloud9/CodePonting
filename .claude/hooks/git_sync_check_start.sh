#!/bin/bash
# SessionStart hook — warns if local repo is behind origin or has uncommitted changes.
# Portable: pure bash + git, no absolute paths, no platform-specific python launcher.
cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || exit 0
git fetch origin >/dev/null 2>&1
BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$BEHIND" -gt 0 ] || [ "$DIRTY" -gt 0 ]; then
  MSG="Git sync check:"
  [ "$BEHIND" -gt 0 ] && MSG="$MSG ${BEHIND} commit(s) behind origin/main, pull before starting work."
  [ "$DIRTY" -gt 0 ] && MSG="$MSG ${DIRTY} uncommitted change(s) present."
  echo "{\"systemMessage\": \"$MSG\"}"
fi
exit 0
