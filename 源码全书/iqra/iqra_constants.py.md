# `iqra/iqra_constants.py`

> 路径：`iqra/iqra_constants.py` | 行数：100


---


```python
#!/usr/bin/env python3
"""
Iqra (إقرأ)
读音: ik-rah（伊克拉）
含义: "你读！"——古兰经降示的第一个词
寓意: Ai 的使命即求知与回应，读尽信息后精准回答

Hermes Constants — Iqra 兼容层

此模块为缺失的 iqra_constants 模块提供存根实现。
原 Hermes 项目中的常量/路径函数在此适配为 Iqra 环境。

所有函数使用惰性/容错实现，确保不会阻塞导入链。
"""

import os
import sys
from pathlib import Path

# ── URL 常量 ──────────────────────────────────────────────────

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# ── 路径函数 ──────────────────────────────────────────────────

def _get_project_root() -> Path:
    """返回项目根目录（iqra/）。"""
    return Path(__file__).resolve().parent


def get_hermes_home() -> Path:
    """返回 Hermes 主目录（适配为 ~/.hermes）。"""
    home = Path.home() / ".hermes"
    return home


def get_hermes_dir() -> Path:
    """返回 Hermes 目录（同 get_hermes_home）。"""
    return get_hermes_home()


def display_hermes_home() -> str:
    """返回 Hermes 主目录的显示路径字符串。"""
    return str(get_hermes_home())


def get_config_path() -> Path:
    """返回 Hermes 配置文件路径。"""
    return get_hermes_home() / "config.yaml"


def get_skills_dir() -> Path:
    """返回技能目录路径。"""
    return get_hermes_home() / "skills"


def get_optional_skills_dir() -> Path:
    """返回可选技能目录路径。"""
    return get_hermes_home() / "optional_skills"


def get_subprocess_home() -> Path:
    """返回子进程 home 目录。"""
    return get_hermes_home() / "subprocess"


# ── 环境检测 ──────────────────────────────────────────────────

def is_termux() -> bool:
    """检测是否为 Termux 环境。Iqra 不在 Termux 运行。"""
    return False


def is_container() -> bool:
    """检测是否为容器环境。"""
    return False


def is_wsl() -> bool:
    """检测是否为 WSL 环境。macOS 上始终为 False。"""
    return False


# ── 辅助函数 ──────────────────────────────────────────────────

def parse_reasoning_effort(effort: str = "medium") -> dict:
    """
    解析 reasoning effort 参数。
    
    Args:
        effort: "low", "medium", "high" 或 None
    
    Returns:
        包含 reasoning_effort 的字典，或空字典
    """
    valid = {"low", "medium", "high"}
    if effort and effort in valid:
        return {"reasoning_effort": effort}
    return {}

```
