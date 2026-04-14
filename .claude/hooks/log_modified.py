"""
PostToolUse hook — silently logs modified file paths.
Fires on every Edit / Write / MultiEdit.
No output. Never blocks.
"""
import sys
import json
import os

MODIFIED_LOG = os.path.join(os.path.dirname(__file__), ".modified_files.txt")

SKIP_PATTERNS = [
    ".claude/", "settings.json", "settings.local.json",
    ".remember/", "PROGRESS", "TODO", "CLAUDE.md", "MEMORY",
    ".obsidian/", "codeponting_structure.md", "README",
    "review_changes.py", "log_modified.py", "scan_modified.py",
    ".modified_files.txt",
]

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    if any(p in file_path for p in SKIP_PATTERNS):
        sys.exit(0)

    # Append to log (dedup handled at scan time)
    try:
        with open(MODIFIED_LOG, "a") as f:
            f.write(file_path + "\n")
    except Exception:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
