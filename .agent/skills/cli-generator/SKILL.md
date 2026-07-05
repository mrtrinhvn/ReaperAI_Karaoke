---
name: cli-generator
description: Meta-skill enabling the Agent to automatically convert local software, repositories, or APIs into structured CLI tools using HKUDS/CLI-Anything.
---

# CLI-Generator (Meta-Skill)

> 🔴 **CRITICAL**: This is a Meta-Skill. It gives you (the AI Agent) the ability to forge your own tools to solve complex constraints.

## When to Use

Use this skill when:
- The user asks you to interact with a complex local GUI software (e.g., GIMP, OBS).
- You are working with a messy, undocumented local API or scripting repository that is too brittle to run manually via ad-hoc scripts.
- You need a dedicated CLI tool to perform repetitive tasks reliably, but none exists.

## The Forging Process

When you decide you need a new CLI tool for a given `TARGET_DIR` (the source code of the application), follow exactly these steps:

### 1. Install CLI-Anything (If not already installed)
Check if `cli-anything` is available in your PATH. If not, install it globally:
```bash
pip install cli-anything
```
*(If the package is not on PyPI, clone `https://github.com/HKUDS/CLI-Anything` and run `pip install -e .`)*

### 2. Run the Generator Pipeline
Navigate to a neutral workspace or the target, and run the automated generation pipeline:
```bash
cli-anything --source /absolute/path/to/TARGET_DIR
```
*Note: This process analyzes the source code and generates the harness. It may take several minutes and uses the underlying LLM's API tokens.*

### 3. Integrate the Forged Skill into `ag-kit`
The pipeline will generate a new Python package (e.g., `cli-anything-targetname`) and automatically produce a `SKILL.md` file within its package directory (usually `cli_anything/<software>/skills/SKILL.md`).
You MUST locate this generated `SKILL.md` and copy it into the user's `ag-kit` workspace:
```bash
mkdir -p .agent/skills/<targetname-cli>
cp /path/to/generated/SKILL.md .agent/skills/<targetname-cli>/SKILL.md
```

### 4. Self-Update
Once the new `SKILL.md` is in place, you (or any other agent using this repository like GravityClaw / Openclaw) will instantly possess the knowledge to use the newly forged CLI tool. Proceed to solve the user's original objective using the new tool natively.

## Anti-Patterns
- ❌ **Manual wrappers**: Do NOT try to manually write a CLI harness or wrappers if `cli-anything` can automate it perfectly.
- ❌ **Token waste**: Do NOT run the generator repeatedly on the same source code. Generate the CLI once, store the `SKILL.md`, and reuse the tool.
