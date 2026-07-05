# Ag-Kit Elite: Next-Generation Agentic Standards

This document defines the advanced agentic standards for Antigravity, synthesized from global top-rated repositories (Aider, OpenHands, Eigent, Continue).

## 1. Context & Search Layer (The "Eyes")
- **Repo Mapping**: Use `.agent/scripts/repomap.py` to get a structural skeleton of the codebase. This is MANDATORY for large-scale refactoring.
- **Semantic Search**: Use the `semantic-search` skill for conceptual discovery when keywords aren't enough.

## 2. Orchestration & Thinking (The "Brain")
- **8-Stage Pipeline**: Follow the **INTAKE → RESEARCH → PLANNING → GENERATION → INTEGRATION → VERIFICATION → REFINEMENT → SHIP** cycle for all `/create` tasks.
- **AgentResult**: Every skill and agent MUST return a standardized JSON result for inter-agent reliability.

## 3. Autonomous Execution (The "Hands")
- **CodeAct Paradigm**: Use `codeact-executor` to write and run scripts in `/tmp` to resolve complex diagnostics before applying fixes.
- **TDD Loop**: Always run tests and fix autonomously using the 8-stage refinement loop.

## 4. Context Containment & Pattern Extraction
- **Smart Learning**: Bạn được phép học giải pháp từ các dự án khác trong `~/Projects/` nhưng PHẢI đảm bảo tính tổng quát hóa.
- **Protocol 3-Bước**: **Quan sát (Bản gốc) -> Lọc bỏ từ khóa riêng (Sanitize) -> Nhân bản chuẩn (Model Pattern)**.
- **Phân tách Linh hồn & Thể xác**: 
    - **Linh hồn (Soul - Local Only):** Các winrate, tên hàm nghiệp vụ lẻ, rulesets riêng biệt. 
    - **Kiến trúc (Architecture - Shared):** Các patterns hạ tầng ( Watchdog, Logger, API wrapper). PHẢI ĐƯỢC TỔNG QUÁT HÓA khi đưa vào Template.

---
> *Antigravity Elite: Synthesized Intelligence for High-Precision Development.*
