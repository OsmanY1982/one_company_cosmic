# `opcclaw/skills/smart_memory/package_skill.py`

> 路径：`opcclaw/skills/smart_memory/package_skill.py` | 行数：58


---


```python
# -*- coding: utf-8 -*-
"""Package smart_memory skill for installation"""
import os
import sys
import zipfile
from datetime import datetime

def package_skill():
    """Package smart_memory skill into .skill file"""
    
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(skill_dir)
    
    # Output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(parent_dir, f"smart_memory_{timestamp}.skill")
    
    # Files to include
    files_to_package = [
        ("SKILL.md", os.path.join(skill_dir, "SKILL.md")),
    ]
    
    # Add core files (referenced by SKILL.md)
    core_dir = os.path.join(skill_dir, "..", "..", "core")
    core_files = [
        "smart_memory.py",
        "smart_memory_adapter.py",
    ]
    
    for f in core_files:
        src = os.path.join(core_dir, f)
        if os.path.exists(src):
            files_to_package.append((f"core/{f}", src))
        else:
            print(f"[WARN] Core file not found: {src}")
    
    # Create zip
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for arcname, src_path in files_to_package:
            if os.path.exists(src_path):
                zf.write(src_path, arcname)
                print(f"[OK] Added: {arcname}")
            else:
                print(f"[ERROR] Missing: {src_path}")
    
    print(f"\n[OK] Skill packaged: {output_file}")
    print(f"[INFO] Size: {os.path.getsize(output_file)} bytes")
    
    # Also create a .zip copy for installation
    zip_copy = output_file.replace('.skill', '.zip')
    import shutil
    shutil.copy2(output_file, zip_copy)
    print(f"[OK] Zip copy: {zip_copy}")
    
    return output_file

if __name__ == '__main__':
    package_skill()

```
