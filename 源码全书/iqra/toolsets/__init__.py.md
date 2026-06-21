# `iqra/toolsets/__init__.py`

> 路径：`iqra/toolsets/__init__.py` | 行数：36


---


```python
"""
toolsets — Iqra 工具集注册中心
从 tools/registry 懒加载所有已注册工具，桥接到 TOOLSETS。
"""

import logging

TOOLSETS: dict = {}
_INITIALIZED = False

logger = logging.getLogger(__name__)


def initialize():
    """从 tools.registry 同步所有已注册工具到 TOOLSETS，幂等。"""
    global _INITIALIZED
    if _INITIALIZED:
        return
    try:
        from tools.registry import registry as _hermes_registry  # type: ignore[import-untyped]
        with _hermes_registry._lock:
            entries = list(_hermes_registry._tools.values())
        for entry in entries:
            TOOLSETS[entry.name] = {
                "name": entry.name,
                "toolset": entry.toolset,
                "schema": entry.schema,
                "handler": entry.handler,
                "description": entry.description,
                "check_fn": entry.check_fn,
            }
        _INITIALIZED = True
        if TOOLSETS:
            logger.info("toolsets loaded %d tools from registry", len(TOOLSETS))
    except Exception:
        logger.debug("toolsets registry bridge skipped (tools/registry not importable)")

```
