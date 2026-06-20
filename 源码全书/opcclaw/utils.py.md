# `opcclaw/utils.py`

> 路径：`opcclaw/utils.py` | 行数：25


---


```python
#!/usr/bin/env python3
"""
utils — OPCclaw 兼容存根
"""

import os

def is_truthy_value(value) -> bool:
    """判断值是否为真值。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)


def atomic_replace(src: str, dst: str):
    """原子替换文件：将 src 移动到 dst，跨文件系统也安全。"""
    try:
        os.replace(src, dst)
    except OSError:
        # 跨文件系统回退：复制后删除
        import shutil
        shutil.copy2(src, dst)
        os.unlink(src)

```
