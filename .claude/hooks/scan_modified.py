"""
Stop hook — final scan reviewer.
Fires once when Claude finishes its turn.
Reads all files modified this turn, reviews each in full.
Silent if clean. Prints only if issues found.
"""
import sys
import json
import subprocess
import os

MODIFIED_LOG = os.path.join(os.path.dirname(__file__), ".modified_files.txt")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "")
if not CLAUDE_BIN:
    candidate = r"C:\Users\Saurav\AppData\Roaming\npm\claude.cmd"
    CLAUDE_BIN = candidate if os.path.exists(candidate) else "claude"

REVIEWER_PROMPT = """\
You are a code reviewer for CodePonting — an NSE intraday equity algo trading system.
Review the complete file below for:

1. LOGIC ERRORS — does the code do what it claims?
2. SILENT FAILURES — wrong variable, off-by-one, condition that never fires, unreachable branch
3. CROSS-DAY DATA LEAKAGE (primary bug class) — any signal component (touch bar,
   bounce bar, entry bar, lookback window) that crosses a calendar day boundary.
   This is intraday-only: ALL components must belong to the SAME trading day.
4. INDEX ERRORS — wrong bar offset in Pine Script or pandas (iloc/loc, shift direction)

File: {file_path}
---
{content}
---

IMPORTANT RULES:
- Only respond if you find a REAL issue. If the file looks correct, respond with exactly: OK
- Do NOT suggest style improvements, refactoring, or missing features.
- Do NOT flag things that are correct just to be thorough.
- If issues exist, respond in this format (one issue per block):
  ISSUE: <one-line description>
  LINE: <line number or function name>
  WHY: <why this is a bug, not just a concern>
"""


def main():
    # Read modified files log
    if not os.path.exists(MODIFIED_LOG):
        sys.exit(0)

    with open(MODIFIED_LOG, "r") as f:
        raw = f.readlines()

    # Clear log immediately (even if review fails, don't re-review next turn)
    os.remove(MODIFIED_LOG)

    # Deduplicate, preserve order
    seen = set()
    files = []
    for line in raw:
        fp = line.strip()
        if fp and fp not in seen and os.path.exists(fp):
            seen.add(fp)
            files.append(fp)

    if not files:
        sys.exit(0)

    issues_found = []

    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            continue

        # Truncate very large files — show first 300 lines
        lines = content.splitlines()
        if len(lines) > 300:
            shown = "\n".join(lines[:300]) + f"\n... ({len(lines)-300} lines truncated)"
        else:
            shown = content

        prompt = REVIEWER_PROMPT.format(file_path=fp, content=shown)

        try:
            result = subprocess.run(
                [CLAUDE_BIN, "-p", "-"],
                input=prompt, capture_output=True, text=True, timeout=90
            )
            verdict = (result.stdout or "").strip()

            if verdict and verdict.upper() != "OK" and "ISSUE:" in verdict:
                issues_found.append((fp, verdict))

        except subprocess.TimeoutExpired:
            pass  # silent on timeout
        except Exception:
            pass  # silent on error

    if issues_found:
        print(f"\n{'═'*60}", file=sys.stderr)
        print(f"  FINAL SCAN — {len(issues_found)} file(s) flagged", file=sys.stderr)
        print(f"{'═'*60}", file=sys.stderr)
        for fp, verdict in issues_found:
            print(f"\n  File: {os.path.basename(fp)}", file=sys.stderr)
            print(f"{'─'*60}", file=sys.stderr)
            print(verdict, file=sys.stderr)
        print(f"\n{'─'*60}", file=sys.stderr)
        print("  Review the above before proceeding. Your call.", file=sys.stderr)
        print(f"{'═'*60}\n", file=sys.stderr)

    sys.exit(0)  # never block — Saurav decides


if __name__ == "__main__":
    main()