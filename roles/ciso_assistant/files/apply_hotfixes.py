#!/usr/bin/env python3
"""
CISO Assistant Hotfix Script
============================
Opravuje chyby v core/models.py - přidává chybějící property settery.

Použití:
    python3 apply_hotfixes.py

Tento skript se spouští uvnitř backend kontejneru.
"""

import sys
import re

FILE_PATH = '/code/core/models.py'


def apply_framework_setter(content, lines):
    """Přidá reference_controls setter do Framework class."""
    if '@reference_controls.setter' in content:
        print("   OK Framework.reference_controls setter jiz existuje")
        return content, False

    new_lines = []
    in_framework = False
    in_ref_controls = False
    inserted = False

    for line in lines:
        new_lines.append(line)
        
        if 'class Framework(' in line:
            in_framework = True
        
        if in_framework and 'def reference_controls(self):' in line:
            in_ref_controls = True
        
        if in_framework and in_ref_controls and 'return reference_controls' in line and not inserted:
            base_indent = "    "
            new_lines.append(f'\n{base_indent}@reference_controls.setter\n')
            new_lines.append(f'{base_indent}def reference_controls(self, value):\n')
            new_lines.append(f'{base_indent}    pass\n')
            inserted = True
            in_ref_controls = False

    if inserted:
        print("   OK Pridan Framework.reference_controls setter")
        return "".join(new_lines), True
    
    return content, False


def apply_mixin_setters(content):
    """Přidá chybějící settery pro ReferentialObjectMixin."""
    setters_to_add = [
        ('get_name_translated', 'self.name = value'),
        ('get_description_translated', 'self.description = value'),
        ('get_annotation_translated', 'self.annotation = value')
    ]
    
    changes_made = False
    
    for prop_name, assignment in setters_to_add:
        setter_sig = f'@{prop_name}.setter'
        
        if setter_sig not in content:
            # Find the property and add setter after it
            lines = content.splitlines(keepends=True)
            new_lines = []
            in_mixin = False
            in_prop = False
            inserted = False
            
            for line in lines:
                new_lines.append(line)
                
                if 'class ReferentialObjectMixin' in line:
                    in_mixin = True
                
                if in_mixin and f'def {prop_name}(self)' in line:
                    in_prop = True
                
                if in_mixin and in_prop and 'return ' in line and not inserted:
                    base_indent = "    "
                    new_lines.append(f'\n{base_indent}@{prop_name}.setter\n')
                    new_lines.append(f'{base_indent}def {prop_name}(self, value):\n')
                    new_lines.append(f'{base_indent}    {assignment}\n')
                    inserted = True
                    in_prop = False
                    changes_made = True
            
            if inserted:
                print(f"   OK Pridan {prop_name} setter")
                content = "".join(new_lines)
        else:
            # Replace 'pass' with proper assignment if needed
            pattern = rf'(@{prop_name}\.setter\s+def {prop_name}\(self, value\):\s+)pass'
            replacement = rf'\1{assignment}'
            content, count = re.subn(pattern, replacement, content)
            if count > 0:
                print(f"   OK Opraven {prop_name} setter (pass -> assignment)")
                changes_made = True
    
    return content, changes_made


def main():
    print("=" * 50)
    print("  CISO ASSISTANT - HOTFIXY")
    print("=" * 50)
    print(f"  Soubor: {FILE_PATH}")
    print("=" * 50)

    try:
        with open(FILE_PATH, 'r') as f:
            content = f.read()
            lines = content.splitlines(keepends=True)

        total_changes = False

        # Fix 1: Framework.reference_controls setter
        content, changed = apply_framework_setter(content, lines)
        total_changes = total_changes or changed
        lines = content.splitlines(keepends=True)

        # Fix 2: ReferentialObjectMixin setters
        content, changed = apply_mixin_setters(content)
        total_changes = total_changes or changed

        if total_changes:
            with open(FILE_PATH, 'w') as f:
                f.write(content)
            print("\n   OK Hotfixy uspesne aplikovany!")
        else:
            print("\n   OK Zadne zmeny nebyly potreba.")

    except FileNotFoundError:
        print(f"   CHYBA: Soubor nenalezen: {FILE_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"   CHYBA: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
