#!/usr/bin/env python3
"""
skill_registry.py — AG-KIT Lazy Skill Activation Engine

Scans all SKILL.md files, extracts frontmatter metadata (name, description,
triggers), and generates a compact registry JSON. AI reads ONLY this registry
(~2KB) instead of all 70 SKILL.md files (~92K tokens).

AI workflow:
  1. Read skills_registry.json (tiny, always loaded)
  2. Match user request against skill triggers
  3. Only THEN read the full SKILL.md of matched skills

Token savings: ~92K → ~0.5K per session (99.5% reduction in skill loading)

Usage:
  python3 skill_registry.py [--root PROJECT_DIR]
  
Output:
  .agent/skills_registry.json
"""

import json
import os
import re
import sys
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    """Extract YAML-like frontmatter from SKILL.md."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    
    fm = {}
    current_key = None
    current_value = []
    
    for line in match.group(1).split('\n'):
        # Handle multi-line values (| or >)
        if current_key and (line.startswith('  ') or line.startswith('\t')):
            current_value.append(line.strip())
            continue
        elif current_key and current_value:
            fm[current_key] = ' '.join(current_value)
            current_key = None
            current_value = []
        
        kv = line.split(':', 1)
        if len(kv) == 2:
            key = kv[0].strip()
            val = kv[1].strip().strip('"').strip("'")
            if val in ('|', '>'):
                current_key = key
                current_value = []
            elif val:
                fm[key] = val
            else:
                fm[key] = ''
    
    if current_key and current_value:
        fm[current_key] = ' '.join(current_value)
    
    return fm


def extract_triggers(content: str) -> list:
    """Extract 'When to Activate' / 'When to Use' triggers from body."""
    triggers = []
    
    # Find "When to Activate/Use" section
    pattern = r'##\s*When to (?:Activate|Use)\s*\n(.*?)(?=\n##|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        for line in match.group(1).split('\n'):
            line = line.strip()
            if line.startswith('- '):
                trigger = line[2:].strip()
                if len(trigger) > 10:  # Skip empty/short lines
                    triggers.append(trigger[:120])  # Cap length
    
    return triggers[:8]  # Max 8 triggers per skill


def scan_skills(skills_dir: Path) -> list:
    """Scan all SKILL.md files and build registry entries."""
    entries = []
    
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        
        try:
            content = skill_md.read_text(encoding='utf-8')
        except Exception:
            continue
        
        fm = parse_frontmatter(content)
        name = fm.get('name', skill_dir.name)
        description = fm.get('description', '')
        
        # Extract triggers
        triggers = extract_triggers(content)
        
        # Detect if skill has executable scripts
        has_scripts = any(
            (skill_dir / d).exists() 
            for d in ['scripts', 'src']
        ) or any(
            f.suffix in ('.py', '.js', '.sh', '.ts')
            for f in skill_dir.rglob('*') if f.is_file()
        )
        
        # Build compact entry
        entry = {
            "name": name,
            "dir": skill_dir.name,
            "desc": description[:200],  # Cap description
        }
        
        if triggers:
            entry["triggers"] = triggers
        
        if has_scripts:
            entry["has_scripts"] = True
        
        # Extract priority if present
        priority = fm.get('priority', '')
        if priority:
            entry["priority"] = priority
        
        entries.append(entry)
    
    return entries

def scan_agents(agents_dir: Path) -> list:
    """Scan all agent .md files and build registry entries."""
    entries = []
    
    for agent_file in sorted(agents_dir.glob("*.md")):
        try:
            content = agent_file.read_text(encoding='utf-8')
        except Exception:
            continue
        
        fm = parse_frontmatter(content)
        name = fm.get('name', agent_file.stem)
        description = fm.get('description', '')
        skills_list = fm.get('skills', '')
        
        # If no description from frontmatter, try first paragraph
        if not description:
            lines = [l.strip() for l in content.split('\n') 
                     if l.strip() and not l.startswith('#') and not l.startswith('---')]
            if lines:
                description = lines[0][:200]
        
        entry = {
            "name": name,
            "file": agent_file.name,
            "desc": description[:200],
        }
        
        if skills_list:
            entry["skills"] = skills_list
        
        entries.append(entry)
    
    return entries


def generate_registry(root: Path) -> dict:
    """Generate the full registry (skills + agents)."""
    skills_dir = root / ".agent" / "skills"
    agents_dir = root / ".agent" / "agents"
    
    skill_entries = scan_skills(skills_dir) if skills_dir.exists() else []
    agent_entries = scan_agents(agents_dir) if agents_dir.exists() else []
    
    # Read pack info if available
    installed_packs = []
    pack_history = root / ".agent" / ".installed_packs"
    if pack_history.exists():
        installed_packs = pack_history.read_text().strip().split(',')
    
    registry = {
        "version": "2.0",
        "total_skills": len(skill_entries),
        "total_agents": len(agent_entries),
        "installed_packs": installed_packs,
        "usage": (
            "AI: Read this registry FIRST at session start. "
            "Match user request against triggers/descriptions. "
            "Only open matched SKILL.md or agent .md files. "
            "DO NOT read all files — this saves ~94% tokens."
        ),
        "skills": skill_entries,
        "agents": agent_entries
    }
    
    return registry



def main():
    import argparse
    parser = argparse.ArgumentParser(description="AG-KIT Skill Registry Generator")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    registry = generate_registry(root)
    
    output = root / ".agent" / "skills_registry.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"📋 Skill Registry: {registry['total_skills']} skills + {registry['total_agents']} agents → {output}")
    
    # Show size comparison
    total_skill_chars = 0
    skills_dir = root / ".agent" / "skills"
    if skills_dir.exists():
        for f in skills_dir.rglob("SKILL.md"):
            try:
                total_skill_chars += f.stat().st_size
            except:
                pass
    
    registry_size = output.stat().st_size
    if total_skill_chars > 0:
        savings = (1 - registry_size / total_skill_chars) * 100
        print(f"   📊 Registry: {registry_size:,} bytes vs All SKILL.md: {total_skill_chars:,} bytes")
        print(f"   💰 Token savings: {savings:.1f}% (AI reads registry first, opens skills on demand)")


if __name__ == "__main__":
    main()
