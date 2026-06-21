# `iqra/tools/xai_http.py`

> 路径：`iqra/tools/xai_http.py` | 行数：12


---


```python
"""Shared helpers for direct xAI HTTP integrations."""

from __future__ import annotations


def hermes_xai_user_agent() -> str:
    """Return a stable Hermes-specific User-Agent for xAI HTTP calls."""
    try:
        from iqra_cli import __version__
    except Exception:
        __version__ = "unknown"
    return f"Hermes-Agent/{__version__}"

```
