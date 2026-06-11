"""
OPCclaw Tool Registry - Enhanced Edition

工具是 OPCclaw 的"手" - LLM 通过 Function Calling 选择工具,
ToolRegistry 负责注册、查找和执行工具。

Enhanced features:
- Execution statistics tracking via PerformanceMonitor
- Tool categories and metadata
- Enable/disable tools dynamically
- Batch execution with error isolation
"""

import json
import time
import traceback
import logging
from typing import Optional, Any, List, Dict, Callable
from .llm_backend import ToolDefinition, ToolCall

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表 - 管理所有可用工具。

    用法:
        registry = ToolRegistry()

        @registry.register("query_orders", "查询订单", {"type": "object", ...})
        def query_orders(month: str) -> dict:
            ...

        # 获取 OpenAI 格式的工具列表喂给 LLM
        tools = registry.to_openai_tools()

        # 执行 LLM 返回的工具调用
        result = registry.execute(tool_call)
    """

    def __init__(self, enable_metrics: bool = True):
        self._tools: Dict[str, ToolDefinition] = {}
        self._disabled_tools: set = set()
        self._categories: Dict[str, str] = {}  # tool_name -> category
        self._enable_metrics = enable_metrics
        self._monitor = None
        
        if enable_metrics:
            try:
                from .performance_monitor import get_monitor
                self._monitor = get_monitor()
            except ImportError:
                self._enable_metrics = False

    # ── 注册 ──

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        category: str = "general",
    ):
        """装饰器: 注册一个工具函数"""
        def decorator(fn):
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                handler=fn,
            )
            self._categories[name] = category
            return fn
        return decorator

    def add_tool(self, tool: ToolDefinition, category: str = "general") -> None:
        """直接添加一个已构建的工具定义"""
        self._tools[tool.name] = tool
        self._categories[tool.name] = category

    def remove_tool(self, name: str) -> bool:
        """移除一个工具"""
        if name in self._tools:
            del self._tools[name]
            self._categories.pop(name, None)
            self._disabled_tools.discard(name)
            return True
        return False

    # ── 启用/禁用 ──

    def enable_tool(self, name: str) -> bool:
        """启用一个之前被禁用的工具"""
        if name in self._tools:
            self._disabled_tools.discard(name)
            return True
        return False

    def disable_tool(self, name: str) -> bool:
        """临时禁用一个工具（不移除定义）"""
        if name in self._tools:
            self._disabled_tools.add(name)
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        """检查工具是否可用"""
        return name in self._tools and name not in self._disabled_tools

    # ── 查询 ──

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self, include_disabled: bool = False) -> List[str]:
        """列出所有工具名，默认不包含禁用的"""
        if include_disabled:
            return list(self._tools.keys())
        return [n for n in self._tools.keys() if n not in self._disabled_tools]

    def list_tools_by_category(self, category: str) -> List[str]:
        """列出某个分类下的所有启用工具"""
        return [
            n for n, c in self._categories.items()
            if c == category and n not in self._disabled_tools
        ]

    def get_categories(self) -> List[str]:
        """获取所有工具分类"""
        return sorted(set(self._categories.values()))

    def count(self) -> int:
        """返回可用工具数量"""
        return len(self.list_tools())

    def count_total(self) -> int:
        """返回包括禁用工具在内的总数"""
        return len(self._tools)

    # ── 转换 ──

    def to_openai_tools(self) -> List[dict]:
        """生成 OpenAI function calling 格式的工具列表（仅启用的工具）"""
        return [
            t.to_openai_schema()
            for name, t in self._tools.items()
            if name not in self._disabled_tools
        ]

    def get_tool_descriptions(self) -> str:
        """生成人类可读的工具描述 (用于 prompt-based tool calling)"""
        lines = []
        for name, t in self._tools.items():
            if name in self._disabled_tools:
                continue
            params_desc = json.dumps(t.parameters, ensure_ascii=False, indent=2)
            category = self._categories.get(name, "general")
            lines.append(f"- {t.name} [{category}]: {t.description}\n  参数: {params_desc}")
        return "\n".join(lines)

    # ── 执行 ──

    def execute(self, tool_call: ToolCall) -> dict:
        """
        执行一个工具调用并返回结果。

        Returns:
            {"success": True, "result": ..., "tool": "xxx"}
            或 {"success": False, "error": "...", "tool": "xxx"}
        """
        tool = self._tools.get(tool_call.name)
        if not tool:
            return {
                "success": False,
                "error": f"未知工具: {tool_call.name}. 可用: {self.list_tools()}",
                "tool": tool_call.name,
            }

        if tool_call.name in self._disabled_tools:
            return {
                "success": False,
                "error": f"工具 {tool_call.name} 已被禁用",
                "tool": tool_call.name,
            }

        if not tool.handler:
            return {
                "success": False,
                "error": f"工具 {tool_call.name} 没有绑定的处理函数",
                "tool": tool_call.name,
            }

        start_time = time.perf_counter()
        try:
            result = tool.handler(**tool_call.arguments)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            if self._monitor:
                self._monitor.record_tool_call(tool_call.name, True, duration_ms)
            logger.debug(f"Tool {tool_call.name} succeeded in {duration_ms:.1f}ms")
            
            return {
                "success": True,
                "result": result,
                "tool": tool_call.name,
                "duration_ms": round(duration_ms, 1),
            }
        except TypeError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self._monitor:
                self._monitor.record_tool_call(tool_call.name, False, duration_ms, str(e))
            
            return {
                "success": False,
                "error": f"参数错误: {e}. 期望参数: {tool.parameters}",
                "tool": tool_call.name,
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {e}"
            if self._monitor:
                self._monitor.record_tool_call(tool_call.name, False, duration_ms, error_msg)
            logger.error(f"Tool {tool_call.name} failed: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "tool": tool_call.name,
                "traceback": traceback.format_exc(),
            }

    def execute_batch(self, tool_calls: List[ToolCall]) -> List[dict]:
        """批量执行多个工具调用，每个独立执行（一个失败不影响其他）"""
        return [self.execute(tc) for tc in tool_calls]

    # ── 统计 ──

    def get_execution_stats(self) -> List[Dict[str, Any]]:
        """获取所有工具的执行统计"""
        if not self._monitor:
            return []
        return self._monitor.get_tool_report()
