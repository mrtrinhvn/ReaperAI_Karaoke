# IDE Adapters — Cross-IDE Compatibility (Auto-managed)

> `.agent/` là Single Source of Truth. Adapter files được **sinh tự động** bởi ag-kit CLI.

## Cách hoạt động

AG-Kit tự động phát hiện IDE đang dùng và sinh adapter file phù hợp.

**Không cần chạy thủ công.** Adapter được tự động sinh khi:
- `ag-kit init` — Khi cài ag-kit vào dự án mới
- `ag-kit update` — Khi nâng cấp ag-kit  
- `ag-kit adapt` — Khi cần sinh/refresh thủ công

## IDE Mapping

| IDE | Entry File | Auto-detect bằng |
|:--|:--|:--|
| **Antigravity** (Google) | `GEMINI.md` | Native — không cần adapter |
| **Cursor** | `.cursorrules` | `.cursor/` dir, `.cursorrules` file, process |
| **Claude Code** (Anthropic) | `CLAUDE.md` | `CLAUDE.md`, `.claude/` dir, process |
| **Windsurf** (Codeium) | `.windsurfrules` | `.windsurfrules` file, process |
| **Aider** | `.aider.conf.yml` | `.aider.conf.yml` file, process |
| **Continue.dev** | `.continue/rules.md` | `.continue/` dir |

## Commands

```bash
ag-kit adapt              # Auto-detect + generate
ag-kit adapt --list       # Show supported IDEs
ag-kit adapt --ide cursor,claude-code  # Force specific IDEs
```

## State tracking

Adapter state lưu tại `.agent/adapters/state.json`:
- `detected_ides` — IDE đã phát hiện
- `generated_files` — Files đã sinh
- `generated_at` — Timestamp
- `ag_kit_version` — Version đã dùng

## Nguyên tắc

1. **Zero manual steps** — Init/Update tự sinh, người dùng không cần biết
2. **Cross-platform** — Node.js (Linux/Mac/Windows), không phụ thuộc bash
3. **Single source of truth** — Rules sống trong `.agent/rules/`, adapter là output
4. **Idempotent** — Chạy lại bao nhiêu lần cũng cho kết quả giống nhau
5. **Process detection** — Quét process đang chạy để tự nhận diện IDE
