#!/usr/bin/env python3
"""
hermes_cli.config — OPCclaw 兼容存根
"""

def cfg_get(key: str, default=None):
    """获取配置值。"""
    defaults = {
        "security.allow_private_urls": False,
        "security.website_blocklist_enabled": False,
        "llm.default_provider": "openai",
    }
    return defaults.get(key, default)
