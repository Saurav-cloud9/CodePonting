#!/usr/bin/env python
"""
CodePonting — Pre-edit reviewer hook
Triggered by: Write, Edit, MultiEdit
Calls a second CC instance to review the diff for logic errors,
silent failures, and cross-day data leakage before the change lands.
"""
import sys
import json
import subprocess
import os

# Files we skip reviewing (infra / config / docs — not strategy logic)
SKIP_PATTERNS = [
    ".claude/", "settings.json", "settings.local.json",
    ".remember/", "PROGRESS", "TODO", "CLAUDE.md", "MEMORY",
    ".obsidian/", "codeponting_structure.md", "README",
    "review_changes.py",  # don't review the reviewer itself
]

REVIEWER_PROMPT = """\
You are a code reviewer for CodePonting — an NSE intraday equity algo trading system.
Review the code change below for:

1. LOGIC ERRORS — does the change do what it claims?
2. SILENT FAILURES — wrong variable used, off-by-one, condition that never fires
3. CROSS-DAY DATA LEAKAGE (primary bug class) — any signal component (touch bar,
   bounce bar, entry bar, lookback window) crossing a calendar day boundary.
   This is intraday-only: all components must belong to the SAME trading day.
4. INDEX ERRORS — wrong bar offset in Pine Script ([0]/[1] confusion) or pandas
   (iloc vs loc, shift direction)

Change to review:
---
{diff}
---

Respond ONLY in this format (3 lines, no extra text):
VERDICT: APPROVE / WARN / REJECT
REASON: <one sentence max>
DETAIL: <specific line or pattern — "none" if APPROVE>
"""


def build_diff(tool_name, tool_input):
    fp = tool_input.get("file_path", "unknown")

    if tool_name == "Write":
        content = tool_input.get("content", "")
        # Truncate very large writes — show first + last 100 lines
        lines = content.splitlines()
        if len(lines) > 200:
            shown = "\n".join(lines[:100]) + f"\n... ({len(lines)-200} lines omitted) ...\n" + "\n".join(lines[-100:])
        else:
            shown = content
        return fp, f"WRITE (full file):\nFile: {fp}\n\n{shown}"

    if tool_name == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        return fp, f"EDIT:\nFile: {fp}\n\n--- REMOVED ---\n{old}\n\n+++ ADDED +++\n{new}"

    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        parts = [f"MULTI-EDIT:\nFile: {fp}"]
        for i, e in enumerate(edits, 1):
            parts.append(f"\n[edit {i}]\n--- REMOVED ---\n{e.get('old_string','')}\n+++ ADDED +++\n{e.get('new_string','')}")
        return fp, "\n".join(parts)

    return fp, ""


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # unparseable input — don't block

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path, diff = build_diff(tool_name, tool_input)

    if not diff:
        sys.exit(0)

    # Skip non-strategy files
    if any(p in file_path for p in SKIP_PATTERNS):
        sys.exit(0)

    prompt = REVIEWER_PROMPT.format(diff=diff)

    try:
        # Use full path — npm bin not always in subprocess PATH on Windows
        claude_bin = os.environ.get("CLAUDE_BIN", "claude")
        if claude_bin == "claude":
            npm_claude = r"C:\Users\Saurav\AppData\Roaming\npm\claude.cmd"
            if os.path.exists(npm_claude):
                claude_bin = npm_claude
        # Pipe prompt via stdin — avoids Windows newline-in-arg issues with claude.cmd
        result = subprocess.run(
            [claude_bin, "-p", "-"],
            input=prompt, capture_output=True, text=True, timeout=90
        )
        verdict_text = (result.stdout or result.stderr or "").strip()

        if not verdict_text:
            print("⚠️  Reviewer returned empty response — proceeding.", file=sys.stderr)
            sys.exit(0)

        fname = os.path.basename(file_path)
        print(f"\n{'═'*60}", file=sys.stderr)
        print(f"  🔍 SECOND REVIEWER (independent CC instance)", file=sys.stderr)
        print(f"  Reviewing: {tool_name} → {fname}", file=sys.stderr)
        print(f"{'─'*60}", file=sys.stderr)
        print(verdict_text, file=sys.stderr)
        print(f"{'─'*60}", file=sys.stderr)
        if "VERDICT: APPROVE" in verdict_text:
            print("  ✅ Reviewer cleared this change. Proceeding.", file=sys.stderr)
        elif "VERDICT: WARN" in verdict_text:
            print("  ⚠️  Reviewer flagged something. Review before finalizing.", file=sys.stderr)
        elif "VERDICT: REJECT" in verdict_text:
            print("  ⛔ Reviewer flagged a critical issue. Change BLOCKED.", file=sys.stderr)
            print("     Fix the issue above, then retry.", file=sys.stderr)
        print(f"{'═'*60}\n", file=sys.stderr)

        if "VERDICT: REJECT" in verdict_text:
            sys.exit(2)  # non-zero blocks the tool

        sys.exit(0)

    except subprocess.TimeoutExpired:
        print("⚠️  Reviewer timed out (90s) — proceeding with change.", file=sys.stderr)
        sys.exit(0)
    except FileNotFoundError:
        print("⚠️  `claude` not found in PATH — reviewer skipped.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"⚠️  Reviewer error: {e} — proceeding with change.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()