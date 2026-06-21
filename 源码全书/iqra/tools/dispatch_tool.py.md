# `iqra/tools/dispatch_tool.py`

> 路径：`iqra/tools/dispatch_tool.py` | 行数：109


---


```python
# -*- coding: utf-8 -*-
"""
dispatch_task 工具 -- 多Agent任务派发

让主AgentLoop可以将子任务按领域派发给专业子Agent执行。
子Agent执行完毕后，结果回传给主Agent继续推进。

用法（由LLM通过Function Calling调用）:
    dispatch_task(
        agent_type="file_agent",
        task="搜索桌面上所有包含'发票'的PDF文件",
        context="用户桌面路径为 /Users/opc/Desktop"
    )
"""

import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# 缓存 backend 和 registry 引用（在注册工具时设置）
_backend = None
_registry = None


def set_dispatch_context(backend, registry) -> None:
    """设置派发上下文（backend和registry引用）"""
    global _backend, _registry
    _backend = backend
    _registry = registry


def dispatch_task(
    agent_type: str,
    task: str,
    context: str = "",
) -> Dict[str, Any]:
    """派发子任务给专业子Agent执行

    Args:
        agent_type: 子Agent类型，可选值:
            - "file_agent": 文件操作专家（搜索/读写/整理/转换）
            - "code_agent": 代码专家（编写/修改/调试/测试）
            - "system_agent": 系统操作专家（配置/进程/诊断）
            - "research_agent": 信息研究专家（搜索/抓取/分析）
            - "general_agent": 通用任务
        task: 子任务描述，应具体、可独立执行
        context: 可选的背景信息（父Agent已知的信息）

    Returns:
        {
            "success": bool,
            "summary": str,        # 子Agent的任务总结
            "files": list[str],    # 涉及的文件路径
            "iterations": int,     # 执行轮数
            "error": str,          # 失败时的错误信息
        }
    """
    from .sub_agent import MiniAgent, SubAgentType

    if _backend is None or _registry is None:
        return {
            "success": False,
            "summary": "",
            "files": [],
            "iterations": 0,
            "error": "派发系统未初始化（backend/registry未设置）",
        }

    # 映射 agent_type 到 SubAgentType
    type_map = {
        "file_agent": SubAgentType.FILE,
        "code_agent": SubAgentType.CODE,
        "system_agent": SubAgentType.SYSTEM,
        "research_agent": SubAgentType.RESEARCH,
        "general_agent": SubAgentType.GENERAL,
    }

    sub_type = type_map.get(agent_type)
    if sub_type is None:
        return {
            "success": False,
            "summary": "",
            "files": [],
            "iterations": 0,
            "error": f"未知的子Agent类型: {agent_type}，可选: {list(type_map.keys())}",
        }

    logger.info(f"派发子任务 → {agent_type}: {task[:80]}...")

    mini = MiniAgent(
        backend=_backend,
        registry=_registry,
        sub_type=sub_type,
        max_rounds=8,  # 子Agent比主Agent更受限
        timeout=120,
    )

    result = mini.run(task, context if context else None)

    # 精简返回给LLM，去掉 raw_output
    return {
        "success": result["success"],
        "summary": result["summary"],
        "files": result.get("files", []),
        "iterations": result["iterations"],
        "error": result.get("error", ""),
    }

```
