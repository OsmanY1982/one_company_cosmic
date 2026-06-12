# `opcclaw/plugins/model-providers/openai-codex/__init__.py`

> 路径：`opcclaw/plugins/model-providers/openai-codex/__init__.py` | 行数：15


---


```python
"""OpenAI Codex (Responses API) provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

openai_codex = ProviderProfile(
    name="openai-codex",
    aliases=("codex", "openai_codex"),
    api_mode="codex_responses",
    env_vars=(),  # OAuth external — no API key
    base_url="https://chatgpt.com/backend-api/codex",
    auth_type="oauth_external",
)

register_provider(openai_codex)

```
