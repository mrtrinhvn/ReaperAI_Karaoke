---
name: Sprint Pipeline
trigger: /sprint
description: |
  Connected workflow pipeline inspired by GStack. 
  Output of each phase feeds into the next phase.
  Think → Plan → Build → Review → Test → Ship → Reflect
---

# /sprint — Sprint Pipeline Workflow

> **Triết lý:** Mỗi bước SẢN SINH output → output đó LÀ input cho bước tiếp theo.
> Không có bước nào chạy cô lập.

## Usage

```
/sprint                    # Start new sprint from Phase 1
/sprint resume             # Resume from last checkpoint
/sprint status             # Show current phase + progress
```

## Pipeline Flow

```
Phase 1: THINK     → Output: problem_statement.md
Phase 2: PLAN      → Output: {task-slug}.md (reads problem_statement)
Phase 3: BUILD     → Output: code changes (reads task-slug.md)
Phase 4: REVIEW    → Output: review_findings.json (reads code diff)
Phase 5: TEST      → Output: test_results.json (reads review findings)
Phase 6: SHIP      → Output: deployment log (reads test results)
Phase 7: REFLECT   → Output: retrospective + decision log entries
```

## Phase Details

### Phase 1: THINK (Socratic Discovery)

**Agent:** None (pure dialogue)
**Input:** User's request
**Output:** `{task-slug}-problem.md`

1. Apply Socratic Gate from `rules/code-workflow.md`
2. Ask minimum 3 strategic questions
3. Identify: Goal, Constraints, Success Criteria, Edge Cases
4. Write problem statement artifact
5. **Gate:** User confirms problem statement before proceeding

### Phase 2: PLAN (Architecture & Design)

**Agent:** `project-planner`
**Input:** `{task-slug}-problem.md`
**Output:** `{task-slug}.md` (task breakdown)

1. Read problem statement from Phase 1
2. Load relevant agent(s) based on domain
3. Break into numbered tasks with dependencies
4. Identify files to modify and test strategy
5. **Gate:** User approves plan before coding

### Phase 3: BUILD (Implementation)

**Agent:** Domain specialist (auto-routed)
**Input:** `{task-slug}.md`
**Output:** Code changes

1. Read task plan from Phase 2
2. Execute tasks in dependency order
3. Mark each task complete as finished
4. Follow `clean-code` rules strictly
5. Log decisions to `.agent/decisions/decisions.jsonl`
6. **No Gate:** Proceed to Review automatically

### Phase 4: REVIEW (Code Audit)

**Agent:** Relevant review specialist(s)
**Input:** Git diff of Phase 3 changes
**Output:** Review findings

1. Auto-detect review scope from changed files:
   - Backend changes → Load `review-specialists/security.md` + `performance.md`
   - API changes → Load `api-contract.md`
   - DB changes → Load `data-migration.md`
   - Frontend → Load `performance.md`
   - >200 lines → Load `maintainability.md`
   - User-facing → Load `red-team.md`
2. Run checklist items against diff
3. Report findings by severity: CRITICAL → INFORMATIONAL
4. **Gate:** Fix CRITICALs before proceeding

### Phase 5: TEST (Verification)

**Agent:** `qa-automation-engineer`
**Input:** Review findings + code changes
**Output:** Test results

1. Load `review-specialists/testing.md`
2. Run existing tests: `python .agent/scripts/test_runner.py .`
3. Check coverage gaps from review findings
4. Write missing tests for new code paths
5. **Gate:** All tests must pass

### Phase 6: SHIP (Deployment)

**Input:** Passing test results
**Output:** Deployment confirmation

1. Run security scan: `python .agent/scripts/security_scan.py .`
2. Run lint: `python .agent/scripts/lint_runner.py .`
3. Git commit with conventional commit message
4. Report deployment status
5. **No Gate:** Proceed to Reflect

### Phase 7: REFLECT (Retrospective)

**Input:** Entire sprint history
**Output:** Decisions + learnings

1. Log durable decisions to `.agent/decisions/decisions.jsonl`
2. Update `.agent/knowledge/` if architecture changed
3. Save learnings to memory MCP
4. Report: What worked, what didn't, what to improve
5. Capture **failed approaches** (what we tried and abandoned)

## Sprint State

Sprint state is saved to `.agent/sprint-state.json`:

```json
{
  "slug": "task-name",
  "current_phase": 3,
  "started": "2026-06-25T10:00:00+07:00",
  "phases_completed": [1, 2],
  "decisions": [1, 2, 3],
  "failed_approaches": ["Tried X but Y happened"]
}
```

## Rules

1. **Never skip phases.** Each phase exists for a reason.
2. **Gates are mandatory.** User must approve at gates (Phases 1, 2, 4, 5).
3. **Log decisions.** Any durable decision → `decision-log.sh log`.
4. **Record failures.** What didn't work is as valuable as what did.
5. **Boil the Ocean.** Always choose the complete implementation.
