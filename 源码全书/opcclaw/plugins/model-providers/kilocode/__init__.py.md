# `opcclaw/plugins/model-providers/kilocode/__init__.py`

> 路径：`opcclaw/plugins/model-providers/kilocode/__init__.py` | 行数：14


---


```python
"""Kilo Code provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

kilocode = ProviderProfile(
    name="kilocode",
    aliases=("kilo-code", "kilo", "kilo-gateway"),
    env_vars=("KILOCODE_API_KEY",),
    base_url="https://api.kilo.ai/api/gateway",
    default_aux_model="google/gemini-3-flash-preview",
)

register_provider(kilocode)

```
