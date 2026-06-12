# `opcclaw/start_opcclaw.py`

> 路径：`opcclaw/start_opcclaw.py` | 行数：18


---


```python
"""
OPCclaw 启动器 - 独立运行版
用法: python start_opcclaw.py
"""
import sys, os

# 加入项目根目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# opcclaw 包在 PROJECT_ROOT 下，所以需要把父目录加入 path
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from opcclaw.modules.chat_window import main

if __name__ == "__main__":
    print("[OPCclaw] Starting...")
    main()
    print("[OPCclaw] Window closed.")

```
