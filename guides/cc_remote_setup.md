# CC Remote Setup — Claude Code

## Auto-launch on Windows Startup

Startup .bat location:
```
C:\Users\Saurav\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\claude_remote.bat
```

## Correct .bat Command

```bat
@echo off
cd /d C:\Users\Saurav\CodePonting
start "Claude Code Remote" cmd /k "claude --dangerously-skip-permissions --name CodePonting"
```

## Bug Fixed (2026-05-06)

| | Detail |
|---|---|
| Broken command | `claude remote-control --permission-mode bypassPermissions --name CodePonting --spawn same-dir` |
| Root cause | `remote-control` is NOT a valid subcommand in v2.1.128 |
| Fix | Remote control activates automatically on CC launch — no extra flags needed |

## Confirmed Working Clients
- Terminal
- VS Code GUI
- Claude.ai CC
- Claude Desktop
