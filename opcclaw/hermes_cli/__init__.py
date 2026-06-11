#!/usr/bin/env python3
"""
hermes_cli.config — OPCclaw 兼容存根

提供 cfg_get() 函数，模拟原 hermes_cli.config 模块的行为。
"""

def cfg_get(key: str, default=None):
    """
    获取配置值。
    
    Args:
        key: 配置键名（支持点分隔符，如 'security.allow_private_urls'）
        default: 默认值
    
    Returns:
        配置值，或默认值
    """
    # OPCclaw 默认配置
    defaults = {
        "security.allow_private_urls": False,
        "security.website_blocklist_enabled": False,
        "llm.default_provider": "openai",
        "llm.temperature": 0.7,
        "memory.enabled": True,
        "skills.auto_inject": True,
    }
    return defaults.get(key, default)
