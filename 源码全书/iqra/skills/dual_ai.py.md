# `iqra/skills/dual_ai.py`

> 路径：`iqra/skills/dual_ai.py` | 行数：28


---


```python
#!/usr/bin/env python3
"""Hermes skill: /dual-ai

Runs dual-AI collaboration using Iqra's DualAIManager.
"""

from dual_ai_collaborator import DualAIManager
import json
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: /dual-ai <task>")
        return
    
    task = ' '.join(sys.argv[1:])
    manager = DualAIManager()
    result = manager.collaborate(task)
    
    # Print clean output for Hermes CLI
    if result.get("success"):
        print(f"✅ Plan:\n{result['plan']}\n\n🚀 Execution:\n{result['execution']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown failure')}")

if __name__ == "__main__":
    main()
```
