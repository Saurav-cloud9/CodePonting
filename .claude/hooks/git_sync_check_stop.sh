#!/bin/bash
# Stop hook — reminds to push if there are unpushed commits or uncommitted changes,
# so switching to another machine (VM/desktop/laptop) doesn't leave work stranded locally.
cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || exit 0
DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
if [ "$DIRTY" -gt 0 ] || [ "$AHEAD" -gt 0 ]; then
  MSG="Git sync check:"
  [ "$AHEAD" -gt 0 ] && MSG="$MSG ${AHEAD} unpushed commit(s)."
  [ "$DIRTY" -gt 0 ] && MSG="$MSG ${DIRTY} uncommitted change(s) - commit and push before switching machines."
  echo "{\"systemMessage\": \"$MSG\"}"
fi
exit 0
