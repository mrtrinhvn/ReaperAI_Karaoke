---
name: bash-linux
description: Bash/Linux terminal rules. Critical commands, error handling, AI Anti-Hang protocol.
priority: P2
---

## When to Activate

- Working on macOS or Linux terminal tasks
- Writing bash scripts

# Bash/Linux Rules

> AI model đã biết bash, grep, find, sed, awk.
> File này = RULES + Anti-Hang Protocol (AI-specific).

---

## Hard Rules

- ✅ `set -euo pipefail` at top of every script
- ✅ Quote ALL variables: `"$VAR"`. CẤM unquoted
- ✅ `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` for relative paths
- ✅ `trap cleanup EXIT` for temp file cleanup
- ✅ `command -v <tool> &> /dev/null` to check if command exists

## Anti-Hang Protocol (AI MANDATORY 🔴)

> AI agents MUST follow these to avoid frozen terminals.

1. **Bypass `rm` alias:** Use `/bin/rm -rf` not `rm -rf` (user may alias `rm -i`)
2. **Cut stdin:** Append `< /dev/null` to commands that might prompt (npm, pkill)
3. **Timeout:** `timeout 15s <command>` for potentially hanging operations

## Quick Reference

| Task | Command |
|---|---|
| Find files | `find . -name "*.js" -type f` |
| Search in files | `grep -rn "pattern" --include="*.js" src/` |
| Kill port | `kill -9 $(lsof -t -i :3000)` |
| Follow log | `tail -f log.txt` |
| Replace in files | `sed -i 's/old/new/g' file.txt` |
| POST JSON | `curl -X POST -H "Content-Type: application/json" -d '{}' URL` |

## Script Template

```bash
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }

main() {
    log_info "Starting..."
    # logic here
    log_info "Done!"
}
main "$@"
```

## Bash vs PowerShell

| Task | Bash | PowerShell |
|---|---|---|
| List files | `ls -la` | `Get-ChildItem` |
| Env vars | `$VAR` | `$env:VAR` |
| Pipeline | Text-based | Object-based |
| Null check | `[ -n "$x" ]` | `if ($x)` |
