#!/usr/bin/env python3
"""
Cognitive Mirror — Tool ID Management Script

Replaces CHANGEME placeholder IDs with real minted IDs from Anna platform.

Usage:
    python scripts/set-tool-id.py apply --tool tool-yourhandle-coherence-engine-xxxx --skill skill-yourhandle-cognitive-coach-xxxx
    python scripts/set-tool-id.py status
    python scripts/set-tool-id.py reset  # use git checkout instead
"""
import argparse
import os
import sys


OLD_TOOL = 'tool-CHANGEME-coherence-engine-CHANGEME'
OLD_SKILL = 'skill-CHANGEME-cognitive-coach-CHANGEME'

FILES_TO_UPDATE = [
    'manifest.json',
    'bundle/app.js',
    'executas/coherence-engine/pyproject.toml',
    'executas/coherence-engine/executa.json',
    'executas/coherence-engine/README.md',
]


def find_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app.json')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("Could not find project root (no app.json found)")


def replace_in_file(filepath, old, new):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old not in content:
        return False
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.replace(old, new))
    return True


def apply_tool_id(tool_id, skill_id=None):
    root = find_project_root()
    updated = []

    print(f"\nApplying tool ID: {tool_id}")
    if skill_id:
        print(f"Applying skill ID: {skill_id}")
    print()

    for filename in FILES_TO_UPDATE:
        filepath = os.path.join(root, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP  {filename} (not found)")
            continue

        changed = False
        if replace_in_file(filepath, OLD_TOOL, tool_id):
            changed = True
        if skill_id and replace_in_file(filepath, OLD_SKILL, skill_id):
            changed = True

        if changed:
            updated.append(filename)
            print(f"  OK    {filename}")
        else:
            print(f"  ---   {filename} (no changes needed)")

    print(f"\n{'=' * 50}")
    print(f"Updated {len(updated)} files")
    print(f"{'=' * 50}")
    print()
    print("Next steps:")
    print(f"  1. Install tool:  cd executas/coherence-engine && uv tool install . --reinstall")
    print(f"  2. Test:          echo '{{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"describe\"}}' | {tool_id}")
    print(f"  3. Run tests:     python tests/test_coherence_engine.py")
    print(f"  4. Deploy:        bash scripts/deploy.sh")


def status(root, tool_id=None, skill_id=None):
    print(f"\nStatus check:")
    for filename in FILES_TO_UPDATE:
        filepath = os.path.join(root, filename)
        if not os.path.exists(filepath):
            print(f"  MISS  {filename}")
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        has_placeholder = OLD_TOOL in content or OLD_SKILL in content
        if has_placeholder:
            print(f"  WARN  {filename} — still has CHANGEME placeholders")
        else:
            print(f"  OK    {filename}")


def main():
    parser = argparse.ArgumentParser(description='Manage Cognitive Mirror Anna tool IDs')
    parser.add_argument('command', choices=['apply', 'reset', 'status'])
    parser.add_argument('--tool', help='Minted tool ID (e.g. tool-yourhandle-coherence-engine-xxxx)')
    parser.add_argument('--skill', help='Minted skill ID (e.g. skill-yourhandle-cognitive-coach-xxxx)')
    args = parser.parse_args()

    if args.command == 'apply':
        if not args.tool:
            print("ERROR: --tool is required for apply command")
            print("  Get your tool ID from: https://anna.partners/executa → My Tools → Create Tool")
            sys.exit(1)
        apply_tool_id(args.tool, args.skill)

    elif args.command == 'reset':
        print("To reset, use git:")
        print("  git checkout -- .")
        print("This restores all CHANGEME placeholders.")

    elif args.command == 'status':
        root = find_project_root()
        status(root, args.tool, args.skill)


if __name__ == '__main__':
    main()
