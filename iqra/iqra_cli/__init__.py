#!/usr/bin/env python3
"""
iqra_cli.config — Iqra 兼容存根

提供 cfg_get() 函数，模拟原 iqra_cli.config 模块的行为。
"""

__version__ = "iqra"


def cfg_get(key: str, default=None):
    """
    获取配置值。
    
    Args:
        key: 配置键名（支持点分隔符，如 'security.allow_private_urls'）
        default: 默认值
    
    Returns:
        配置值，或默认值
    """
    # Iqra 默认配置
    defaults = {
        "security.allow_private_urls": False,
        "security.website_blocklist_enabled": False,
        "llm.default_provider": "openai",
        "llm.temperature": 0.7,
        "memory.enabled": True,
        "skills.auto_inject": True,
    }
    return defaults.get(key, default)
