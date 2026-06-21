# `iqra/plugins/model-providers/xiaomi/__init__.py`

> 路径：`iqra/plugins/model-providers/xiaomi/__init__.py` | 行数：13


---


```python
"""Xiaomi MiMo provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

xiaomi = ProviderProfile(
    name="xiaomi",
    aliases=("mimo", "xiaomi-mimo"),
    env_vars=("XIAOMI_API_KEY",),
    base_url="https://api.xiaomimimo.com/v1",
)

register_provider(xiaomi)

```
