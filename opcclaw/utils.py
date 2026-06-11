#!/usr/bin/env python3
"""
utils — OPCclaw 兼容存根
"""

def is_truthy_value(value) -> bool:
    """判断值是否为真值。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)
