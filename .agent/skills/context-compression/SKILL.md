---
name: context-compression
description: Manage and compress conversation context in long sessions. Detect when context is growing large, summarize completed work phases, archive old findings while preserving key decisions. Prevents context degradation.
when_to_use: "When a session has 20+ turns, when context feels repetitive, when the agent is losing track of earlier work, or when the user says 'tóm tắt lại' or 'summarize what we've done'. NOT for short sessions."
allowed-tools: Read, Write, Grep
effort: low
---



## When to Activate

- Manage and compress conversation context in long sessions. Detect when context is growing large, summarize completed wor
- Need guidance on: When to Compress
- Need guidance on: Research Phase Complete (Bamboo Airways Booking Debug)
- Need guidance on: Session Checkpoint (Turn 35)
- Need guidance on: Compression Rules

> Keep sessions productive by compressing completed work while preserving key decisions.

## Overview
Long sessions (30+ turns) cause context degradation — the AI loses track of earlier work, repeats itself, or forgets decisions. Context compression proactively summarizes completed phases so the context window stays focused on active work.

**Token Impact:** Recovers 5,000-15,000 tokens in long sessions by replacing verbose tool outputs with semantic summaries.

---

## When to Compress
| Signal | Action |
|---|---|
| Session has 20+ turns | Consider proactive compression |
| Agent repeats earlier suggestions | Context is saturated — compress now |
| User says "mình đã thảo luận rồi" | Compress immediately |
| Switching to a new phase of work | Compress the completed phase |
| Large tool output (500+ lines) | Micro-compact the output |

---

### Level 1: Micro-Compact (Tool Output)
Compress individual tool outputs while retaining semantic content:

```
❌ Before (raw grep output — 200 lines, ~4,000 tokens):
src/services/ags99/booking.ts:15: import { verify } from 'jsonwebtoken'
...

✅ After (micro-compact — 5 lines, ~100 tokens):
Grep results for "hanh_khach": Found in 3 files.
Key: booking.ts:113 (payload build), booking.ts:234 (validation check).
Issue: Field missing when airline === 'QH' due to branch not populating pArray.
```

### Level 2: Phase Summary
Replace a completed work phase with a summary:

```
❌ Before (full research transcript — ~3,000 tokens):
[turn 1] Read booking.ts...
[turn 2] Run test-search-and-book.ts...
[turn 3] Got "Not enough segments" error...

✅ After (phase summary — ~200 tokens):
## Research Phase Complete (Bamboo Airways Booking Debug)
- AGS99 /v3/dat-chuyen requires Fernet-encrypted body with {payload: "gAAAA..."}
- BUT: backend actually expects raw JSON array (not encrypted wrapper)
- /v1/th/v1/danh-sach-ghe needs to be called first to register UUID in session
- "Not enough segments" = session UUID not registered
- Bug: seatPayload format wrong — needs [{airline, data, ma_diem_di}] structure
```

### Level 3: Session Checkpoint
Full session summary for long-running work:

```markdown
## Session Checkpoint (Turn 35)

### Completed
- [x] Researched AGS99 auth/encryption protocol
- [x] Identified "Not enough segments" root cause
- [x] Fixed encryptPayload wrapper issue in test-search-and-book.ts

### In Progress
- [ ] Fix danh-sach-ghe payload format for QH airline
- [ ] Test end-to-end booking flow

### Key Decisions
1. Don't encrypt the /v3/dat-chuyen body — send raw JSON array
2. danh-sach-ghe must be called with [{airline, data, ma_diem_di}] format
3. Use decryptPayload() only for reading responses, not for sending requests

### Files Modified
- server-node/test-search-and-book.ts (payload structure)
- server-node/test-booking-real.ts (contactInfo schema fix)
```

---

## Compression Rules
1. **Compress phases, not facts** — Individual decisions should stay, full transcripts should go
2. **Preserve "why" over "what"** — Why a decision was made matters more than the exact commands run
3. **Never auto-compress** — Always tell the user "Em đang tóm tắt phase research để tiết kiệm context"
4. **Keep file references** — Always preserve file paths and line numbers in summaries
5. **Checkpoint on phase transitions** — Natural compression point when switching from research to implementation
