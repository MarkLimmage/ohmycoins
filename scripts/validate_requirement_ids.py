#!/usr/bin/env python3
"""
Validate that all REQ-XX-YYY references in code exist in SYSTEM_REQUIREMENTS.md
"""
import re
import sys
from pathlib import Path


def find_requirement_references(root_dir):
    """Scan code for REQ-XX-YYY patterns"""
    pattern = re.compile(r'REQ-[A-Z]+-[A-Z]+-[0-9]+|REQ-[A-Z]+-[0-9]+')
    refs = set()
    
    # Scan Python files
    for path in Path(root_dir).rglob('*.py'):
        if 'venv' in str(path) or '.venv' in str(path) or '__pycache__' in str(path):
            continue
        try:
            content = path.read_text()
            refs.update(pattern.findall(content))
        except Exception:
            pass
    
    # Scan TypeScript/JavaScript files
    for ext in ['*.tsx', '*.ts', '*.jsx', '*.js']:
        for path in Path(root_dir).rglob(ext):
            if 'node_modules' in str(path) or 'dist' in str(path):
                continue
            try:
                content = path.read_text()
                refs.update(pattern.findall(content))
            except Exception:
                pass
    
    # Scan markdown files
    for path in Path(root_dir).rglob('*.md'):
        if '.venv' in str(path) or 'node_modules' in str(path):
            continue
        try:
            content = path.read_text()
            refs.update(pattern.findall(content))
        except Exception:
            pass
    
    return refs


def find_defined_requirements(srs_path):
    """Extract all defined requirements from SYSTEM_REQUIREMENTS.md"""
    content = Path(srs_path).read_text()
    
    # Match table format: | REQ-XX-YYY | or | REQ-XX-YYY-ZZZ |
    pattern = re.compile(r'\|\s+(REQ-[A-Z]+-[A-Z]+-[0-9]+|REQ-[A-Z]+-[0-9]+)\s+\|')
    defined = set(pattern.findall(content))
    
    # Also match bold format: **REQ-XX-YYY**:
    pattern2 = re.compile(r'\*\*(REQ-[A-Z]+-[A-Z]+-[0-9]+|REQ-[A-Z]+-[0-9]+)\*\*:')
    defined.update(pattern2.findall(content))
    
    return defined


def main():
    root_dir = Path('.')
    srs_path = Path('docs/SYSTEM_REQUIREMENTS.md')
    
    if not srs_path.exists():
        print(f"❌ SYSTEM_REQUIREMENTS.md not found at {srs_path}")
        sys.exit(1)
    
    refs = find_requirement_references(root_dir)
    defined = find_defined_requirements(srs_path)
    
    # Filter out common false positives (template examples)
    refs = {r for r in refs if not any(x in r for x in ['XX', 'YYY', 'ZZZ'])}
    
    undefined = refs - defined
    
    if undefined:
        print("❌ Found undefined requirement references:")
        for req in sorted(undefined):
            print(f"  - {req}")
        print(f"\n{len(undefined)} undefined requirements found")
        print("\nPlease add these requirements to SYSTEM_REQUIREMENTS.md")
        sys.exit(1)
    
    print(f"✅ All {len(refs)} requirement references validated")
    print(f"   Defined in SYSTEM_REQUIREMENTS.md: {len(defined)}")
    print(f"   Referenced in code/docs: {len(refs)}")


if __name__ == '__main__':
    main()
