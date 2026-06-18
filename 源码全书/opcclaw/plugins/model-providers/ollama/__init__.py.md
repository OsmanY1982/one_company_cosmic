# `opcclaw/plugins/model-providers/ollama/__init__.py`

> 路径：`opcclaw/plugins/model-providers/ollama/__init__.py` | 行数：80


---


```python
"""Ollama 本地推理 provider profile.

Separate from "custom" — gives Ollama its own top-level entry in the
model settings UI, defaulting to localhost:11434 and using /api/tags
for model discovery.
"""

from __future__ import annotations

from typing import Any
import http.client
import json

from providers import register_provider
from providers.base import ProviderProfile


class OllamaProfile(ProviderProfile):
    """Ollama 本地推理 — /api/tags model discovery, 11434 default."""

    def build_api_kwargs_extras(
        self,
        *,
        reasoning_config: dict | None = None,
        ollama_num_ctx: int | None = None,
        **ctx: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        extra_body: dict[str, Any] = {}

        if ollama_num_ctx:
            options = extra_body.get("options", {})
            options["num_ctx"] = ollama_num_ctx
            extra_body["options"] = options

        if reasoning_config and isinstance(reasoning_config, dict):
            _effort = (reasoning_config.get("effort") or "").strip().lower()
            _enabled = reasoning_config.get("enabled", True)
            if _effort == "none" or _enabled is False:
                extra_body["think"] = False

        return extra_body, {}

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        """Discover models via Ollama /api/tags endpoint."""
        import urllib.parse

        url = urllib.parse.urlparse(self.base_url or "http://localhost:11434/v1")
        host = url.hostname or "localhost"
        port = url.port or 11434

        conn: http.client.HTTPConnection | None = None
        try:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
            conn.request("GET", "/api/tags")
            resp = conn.getresponse()
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode())
            models = data.get("models", [])
            return [m["name"] for m in models if m.get("name")]
        except Exception:
            return None
        finally:
            if conn:
                conn.close()


ollama = OllamaProfile(
    name="ollama",
    aliases=("ollama-local", "ollama_local"),
    env_vars=(),  # no API key needed for local Ollama
    base_url="http://localhost:11434/v1",
)

register_provider(ollama)

```
