# `opcclaw/tools/browser_providers/__init__.py`

> 路径：`opcclaw/tools/browser_providers/__init__.py` | 行数：10


---


```python
"""Cloud browser provider abstraction.

Import the ABC so callers can do::

    from tools.browser_providers import CloudBrowserProvider
"""

from tools.browser_providers.base import CloudBrowserProvider

__all__ = ["CloudBrowserProvider"]

```
