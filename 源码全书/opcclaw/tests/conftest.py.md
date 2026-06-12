# `opcclaw/tests/conftest.py`

> 路径：`opcclaw/tests/conftest.py` | 行数：7


---


```python
"""Ensure opcclaw package root is on sys.path for imports."""
import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

```
