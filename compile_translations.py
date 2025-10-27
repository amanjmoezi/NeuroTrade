#!/usr/bin/env python3
"""
Compile .po translation files to .mo binary files
Run this script after updating translation files
"""
import os
import subprocess
from pathlib import Path


def compile_translations():
    """Compile all .po files to .mo files"""
    project_root = Path(__file__).parent
    locales_dir = project_root / 'locales'
    
    if not locales_dir.exists():
        print(f"❌ Locales directory not found: {locales_dir}")
        return
    
    # Find all .po files
    po_files = list(locales_dir.rglob('*.po'))
    
    if not po_files:
        print(f"⚠️  No .po files found in {locales_dir}")
        return
    
    print(f"📦 Compiling {len(po_files)} translation files...")
    
    compiled_count = 0
    for po_file in po_files:
        # Output .mo file in the same directory
        mo_file = po_file.with_suffix('.mo')
        
        try:
            # Use msgfmt to compile
            result = subprocess.run(
                ['msgfmt', str(po_file), '-o', str(mo_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Compiled: {po_file.relative_to(project_root)} → {mo_file.name}")
                compiled_count += 1
            else:
                print(f"❌ Error compiling {po_file.name}:")
                print(result.stderr)
        except FileNotFoundError:
            print("❌ msgfmt not found. Please install gettext:")
            print("   Ubuntu/Debian: sudo apt-get install gettext")
            print("   macOS: brew install gettext")
            print("   Or use Python's babel:")
            print("   pip install Babel")
            print("   Then run: pybabel compile -d locales -D messages")
            return
        except Exception as e:
            print(f"❌ Error compiling {po_file.name}: {e}")
    
    print(f"\n🎉 Successfully compiled {compiled_count}/{len(po_files)} translation files!")


def compile_with_babel():
    """Alternative: Compile using Babel (pure Python)"""
    try:
        from babel.messages import mofile, pofile
        print("Using Babel to compile translations...")
        
        project_root = Path(__file__).parent
        locales_dir = project_root / 'locales'
        
        compiled_count = 0
        # Compile for each language
        for lang_dir in locales_dir.iterdir():
            if lang_dir.is_dir() and (lang_dir / 'LC_MESSAGES' / 'messages.po').exists():
                po_file_path = lang_dir / 'LC_MESSAGES' / 'messages.po'
                mo_file_path = lang_dir / 'LC_MESSAGES' / 'messages.mo'
                
                try:
                    with open(po_file_path, 'rb') as po_file:
                        catalog = pofile.read_po(po_file, locale=lang_dir.name)
                    
                    with open(mo_file_path, 'wb') as mo_file:
                        mofile.write_mo(mo_file, catalog)
                    
                    print(f"✅ Compiled: {lang_dir.name} ({po_file_path.relative_to(project_root)} → {mo_file_path.name})")
                    compiled_count += 1
                except Exception as e:
                    print(f"❌ Error compiling {lang_dir.name}: {e}")
        
        print(f"\n🎉 Successfully compiled {compiled_count} translation files!")
    except ImportError:
        print("❌ Babel not installed. Install it with: pip install Babel")


if __name__ == '__main__':
    import sys
    
    # Try msgfmt first, fall back to Babel
    if '--babel' in sys.argv or not subprocess.run(['which', 'msgfmt'], capture_output=True).returncode == 0:
        compile_with_babel()
    else:
        compile_translations()
