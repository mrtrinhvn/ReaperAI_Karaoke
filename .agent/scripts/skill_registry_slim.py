#!/usr/bin/env python3
"""
skill_registry_slim.py — Generate compact skill registry for token-efficient routing.

Before: 43,329 chars (~10,832 tokens) — full triggers, descriptions
After:  ~13,000 chars (~3,300 tokens) — name + 80-char desc + priority

Usage:
  python3 skill_registry_slim.py --root .
  python3 skill_registry_slim.py --root . --full   # Also generate full version
"""

import json
import os
import re
import sys
import argparse


def extract_skill_meta(skill_dir):
    """Extract name and description from SKILL.md frontmatter."""
    skill_md = os.path.join(skill_dir, 'SKILL.md')
    if not os.path.exists(skill_md):
        return None

    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    name = os.path.basename(skill_dir)
    desc = ''
    priority = 'P2'

    # Parse YAML frontmatter
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        # Extract description (handle YAML multiline | and >)
        desc_match = re.search(r'description:\s*(.*?)$', fm, re.MULTILINE)
        if desc_match:
            first_line = desc_match.group(1).strip().strip('"').strip("'")
            if first_line in ('|', '>', '|-', '>-'):
                # YAML multiline block — read indented continuation lines
                lines_after = fm[desc_match.end():].split('\n')
                multiline_parts = []
                for line in lines_after:
                    if not line.strip():
                        continue  # skip empty lines
                    if line[0] == ' ' or line[0] == '\t':
                        multiline_parts.append(line.strip())
                    else:
                        break
                desc = ' '.join(multiline_parts)
            else:
                desc = first_line
        # Extract priority
        prio_match = re.search(r'priority:\s*(\S+)', fm, re.IGNORECASE)
        if prio_match:
            pval = prio_match.group(1).upper()
            if 'CRITICAL' in pval or 'P0' in pval:
                priority = 'P0'
            elif 'HIGH' in pval or 'P1' in pval:
                priority = 'P1'

    # Truncate description to 80 chars
    if len(desc) > 80:
        desc = desc[:77] + '...'

    return {'n': name, 'd': desc, 'p': priority}


def extract_agent_meta(agent_file):
    """Extract agent name, description, and skill list."""
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()

    name = os.path.basename(agent_file).replace('.md', '')
    desc = ''
    skills = ''

    # Extract description from frontmatter or first paragraph
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        desc_match = re.search(r'description:\s*(.*?)$', fm, re.MULTILINE)
        if desc_match:
            first_line = desc_match.group(1).strip().strip('"').strip("'")
            if first_line in ('|', '>', '|-', '>-'):
                lines_after = fm[desc_match.end():].split('\n')
                multiline_parts = []
                for line in lines_after:
                    if not line.strip():
                        continue
                    if line[0] == ' ' or line[0] == '\t':
                        multiline_parts.append(line.strip())
                    else:
                        break
                desc = ' '.join(multiline_parts)
            else:
                desc = first_line
        skills_match = re.search(r'skills:\s*(.*?)$', fm, re.MULTILINE)
        if skills_match:
            skills = skills_match.group(1).strip()

    if len(desc) > 80:
        desc = desc[:77] + '...'

    return {'n': name, 'd': desc, 's': skills}


def build_slim_registry(root_dir):
    """Build the slim registry from .agent/ directory."""
    agent_dir = os.path.join(root_dir, '.agent')
    skills_dir = os.path.join(agent_dir, 'skills')
    agents_dir = os.path.join(agent_dir, 'agents')

    # Read ag-kit version from .agent/.version (stamped during init/update)
    version = '2.2.8'
    version_file = os.path.join(agent_dir, '.version')
    if os.path.exists(version_file):
        try:
            version = open(version_file).read().strip()
        except Exception:
            pass

    registry = {
        'v': version,
        'skills': [],
        'agents': []
    }

    # Process skills
    if os.path.isdir(skills_dir):
        for skill_name in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, skill_name)
            if not os.path.isdir(skill_path):
                continue
            meta = extract_skill_meta(skill_path)
            if meta:
                registry['skills'].append(meta)

    # Process agents
    if os.path.isdir(agents_dir):
        for agent_file in sorted(os.listdir(agents_dir)):
            if not agent_file.endswith('.md'):
                continue
            agent_path = os.path.join(agents_dir, agent_file)
            meta = extract_agent_meta(agent_path)
            if meta:
                registry['agents'].append(meta)

    return registry


def main():
    parser = argparse.ArgumentParser(description='Generate slim skill registry')
    parser.add_argument('--root', default='.', help='Project root directory')
    parser.add_argument('--full', action='store_true', help='Also keep full registry')
    parser.add_argument('--output', help='Output file path')
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    agent_dir = os.path.join(root, '.agent')

    if not os.path.isdir(agent_dir):
        print("❌ .agent/ directory not found", file=sys.stderr)
        sys.exit(1)

    # Build slim registry
    slim = build_slim_registry(root)

    # Output path
    output = args.output or os.path.join(agent_dir, 'skills_registry.json')

    # If --full, backup the original
    if args.full and os.path.exists(output):
        full_path = output.replace('.json', '_full.json')
        with open(output, 'r') as f:
            full_data = json.load(f)
        with open(full_path, 'w') as f:
            json.dump(full_data, f, indent=2, ensure_ascii=False)
        print(f"📋 Full registry backed up to {os.path.basename(full_path)}")

    # Write slim registry
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(slim, f, indent=2, ensure_ascii=False)

    size = os.path.getsize(output)
    tokens = size // 4
    print(f"✅ Slim registry: {len(slim['skills'])} skills, {len(slim['agents'])} agents")
    print(f"   Size: {size:,} bytes (~{tokens:,} tokens)")

    # Compare with old if exists
    full_path = output.replace('.json', '_full.json')
    if os.path.exists(full_path):
        old_size = os.path.getsize(full_path)
        savings = old_size - size
        print(f"   Savings: {savings:,} bytes (~{savings//4:,} tokens, {savings*100//old_size}% reduction)")


if __name__ == '__main__':
    main()
