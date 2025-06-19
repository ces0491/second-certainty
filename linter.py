#!/usr/bin/env python3
"""
Script to fix the remaining flake8 issues in the Second Certainty project.
"""

import os
import re
from pathlib import Path


def fix_inline_comments(file_path: Path) -> bool:
    """Fix E262 inline comment spacing issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix inline comments: ensure proper spacing before #
            # Pattern: non-whitespace character followed by # without proper spacing
            if '#' in line and not line.strip().startswith('#'):
                # Replace patterns like "code#comment" with "code  # comment"
                line = re.sub(r'(\S)#([^#\s])', r'\1  # \2', line)
                # Replace patterns like "code #comment" with "code  # comment"  
                line = re.sub(r'(\S) #([^#\s])', r'\1  # \2', line)
            
            fixed_lines.append(line)
        
        new_content = '\n'.join(fixed_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Fixed inline comments in: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False


def fix_migration_comments(file_path: Path) -> bool:
    """Fix E266 issues in migration files (too many leading #)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix lines with multiple ### to single #
            if re.match(r'^\s*#+\s*[A-Za-z]', line):
                # Replace multiple # with single # and space
                line = re.sub(r'^(\s*)#+\s*', r'\1# ', line)
            
            fixed_lines.append(line)
        
        new_content = '\n'.join(fixed_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Fixed migration comments in: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False


def remove_safe_unused_imports():
    """Remove obviously unused imports that are safe to remove."""
    
    safe_removals = {
        'app/core/config.py': ['typing.List'],
        'app/core/scraping/sars_service.py': ['typing.Tuple'],
        'app/core/scraping/tax_repository.py': ['typing.List'],
        'app/core/scraping/web_client.py': ['typing.Any', 'typing.Dict'],
        'app/core/tax_calculator.py': ['typing.Tuple'],
    }
    
    for file_path, imports_to_remove in safe_removals.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            filtered_lines = []
            for line in lines:
                should_keep = True
                for import_name in imports_to_remove:
                    if f"'{import_name}'" in line or f'"{import_name}"' in line:
                        if line.strip().startswith(('from typing import', 'import typing')):
                            # Remove just this import from the line
                            line = re.sub(rf',?\s*{re.escape(import_name.split(".")[-1])},?', '', line)
                            # Clean up any resulting double commas or trailing commas
                            line = re.sub(r',\s*,', ',', line)
                            line = re.sub(r',\s*\)', ')', line)
                            line = re.sub(r'\(\s*,', '(', line)
                            # If line becomes empty import, skip it
                            if re.match(r'^\s*from\s+\w+\s+import\s*\(\s*\)\s*$', line):
                                should_keep = False
                
                if should_keep and line.strip():
                    filtered_lines.append(line)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            
            print(f"✓ Cleaned unused imports in: {file_path}")
            
        except Exception as e:
            print(f"✗ Error cleaning {file_path}: {e}")


def fix_unused_variable():
    """Fix the unused variable in tax_utils.py."""
    file_path = 'app/utils/tax_utils.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove or use the unused variable
        # Option 1: Remove the assignment if not needed
        content = re.sub(r'\s*current_year\s*=\s*[^\n]+\n', '', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Fixed unused variable in: {file_path}")
        
    except Exception as e:
        print(f"✗ Error fixing unused variable in {file_path}: {e}")


def main():
    """Run all remaining fixes."""
    print("🔧 Applying remaining flake8 fixes...")
    
    # Fix inline comments in all Python files
    python_files = list(Path('app').rglob("*.py"))
    
    fixes_applied = 0
    
    for file_path in python_files:
        if fix_inline_comments(file_path):
            fixes_applied += 1
    
    # Fix migration-specific issues
    migration_files = list(Path('app/db/migrations/versions').glob("*.py"))
    for file_path in migration_files:
        if fix_migration_comments(file_path):
            fixes_applied += 1
    
    # Remove safe unused imports
    remove_safe_unused_imports()
    
    # Fix unused variable
    fix_unused_variable()
    
    print(f"\n✅ Applied fixes to {fixes_applied} files.")
    
    print("\n📋 Manual review needed for:")
    print("1. app/db/base.py - Database model imports (keep these)")
    print("2. app/main.py - Application initialization imports")
    print("3. app/db/migrations/env.py - Migration imports and positioning")
    print("4. Migration files - some 'unused' imports are required by Alembic")
    
    print("\n🔍 Run this to check remaining issues:")
    print("flake8 --max-line-length=120 --extend-ignore=E203,W503 app")


if __name__ == "__main__":
    main()