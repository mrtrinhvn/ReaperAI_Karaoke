---
name: codeact-executor
description: Autonomous script execution for complex problem solving (Code-as-Action).
version: 1.0.0
---



## When to Activate

- Autonomous script execution for complex problem solving (Code-as-Action).
- Working on code-related tasks
- Need guidance on: Core Principle
- Need guidance on: Workflow
- Need guidance on: Safety Protocols

# CodeAct Executor

**Purpose**: Allow specialist agents to solve complex problems by writing and executing Python or Bash scripts in a controlled environment. This is safer and more flexible than simple file editing.

## Core Principle

> **Code is the ultimate tool.** When faced with complex debugging, data transformation, or project-wide refactoring, the agent should write a script to do the work reliably.

## Workflow

1. **Draft**: Agent writes a script (`/tmp/solve_problem.py`).
2. **Execute**: Agent runs the script and captures output.
3. **Analyze**: Agent reviews the output/logs.
4. **Iterate**: If the script failed, the agent fixes it and re-runs.
5. **Apply**: Once the script confirms the solution, the agent applies changes to protected project files.

## Safety Protocols

> [!WARNING]
> **Sandboxing Required**: In production, all CodeAct executions MUST run in a Docker sandbox. Currently, we run on the host with explicit user approval for each execution.

- **Check PIDs**: Avoid scripts that run endless loops.
- **FS Isolation**: Scripts should primarily work in `/tmp/` before touching project files.
- **Resource Limits**: Kill scripts that exceed 30 seconds or high memory.

## Examples

### Case 1: Complex Refactoring
Agent writes a Python script using `ast` to rename a class across 50 files and update all imports.

### Case 2: Data Extraction
Agent writes a script to scrape an internal API and generate a JSON schema from the response.

### Case 3: Performance Profiling
Agent writes a benchmark script to measure the execution time of two different algorithms.
