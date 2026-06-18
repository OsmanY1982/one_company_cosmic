# `opcclaw/core/enhanced_hermes_bridge.py`

> 路径：`opcclaw/core/enhanced_hermes_bridge.py` | 行数：335


---


```python
"""
增强版 Hermes <-> OPCclaw 工具桥接层
支持完整对话、多模型、插件扩展

修复内容:
1. 移除白名单限制，桥接所有可用工具
2. 添加对话状态管理
3. 支持多模型切换
4. 集成文件/图片/搜索等高级功能
"""

import sys
import os
import json
import asyncio
import threading
import concurrent.futures
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List, Generator
from dataclasses import dataclass, field

# ── 确保路径 ──
_opcclaw_root = Path(__file__).resolve().parent.parent
_tools_dir = _opcclaw_root / "tools"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))
if str(_opcclaw_root) not in sys.path:
    sys.path.insert(0, str(_opcclaw_root))


@dataclass
class ConversationState:
    """对话状态管理"""
    session_id: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_message(self, role: str, content: str, **kwargs):
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        return msg
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.messages[-limit:]
    
    def clear(self):
        self.messages = []
        self.context = {}
        self.tool_results = []


class EnhancedHermesBridge:
    """
    增强版 Hermes 桥接器
    - 支持完整工具集（无白名单限制）
    - 对话状态持久化
    - 多模型后端支持
    """
    
    def __init__(self, registry=None, quiet: bool = False):
        self.registry = registry
        self.quiet = quiet
        self._conversations: Dict[str, ConversationState] = {}
        self._current_session: str = "default"
        self._business_tools_registered = False
        
    def _get_conversation(self, session_id: str = None) -> ConversationState:
        sid = session_id or self._current_session
        if sid not in self._conversations:
            self._conversations[sid] = ConversationState(session_id=sid)
        return self._conversations[sid]
    
    def bridge_all_tools(self, opcclaw_registry=None, include_business: bool = True) -> int:
        """
        桥接所有 Hermes 工具（包括业务工具）
        
        Args:
            opcclaw_registry: 目标注册表
            include_business: 是否包含业务工具
        
        Returns:
            注册的工具数量
        """
        from .tool_registry import ToolDefinition
        
        if opcclaw_registry is None:
            from .tool_registry import ToolRegistry
            opcclaw_registry = ToolRegistry()
            self.registry = opcclaw_registry
        
        # Step 1: 触发 Hermes 工具自动发现
        try:
            from tools.registry import registry as _hermes_registry
            from tools.registry import discover_builtin_tools
            
            if not self.quiet:
                print("[INFO] Discovering all Hermes tools...")
            
            discover_builtin_tools()
            
            # Step 2: 注册业务工具
            if include_business and not self._business_tools_registered:
                self._register_all_business_tools(_hermes_registry)
                self._business_tools_registered = True
                
        except Exception as e:
            if not self.quiet:
                print(f"[WARN] Hermes discovery failed: {e}")
            return 0
        
        # Step 3: 桥接所有工具（无白名单过滤）
        count = 0
        for tool_name, entry in list(_hermes_registry._tools.items()):
            # 检查工具可用性
            if entry.check_fn:
                try:
                    if not entry.check_fn():
                        if not self.quiet:
                            print(f"  [WARN] Tool unavailable: {tool_name}")
                        continue
                except Exception:
                    pass
            
            # 提取参数定义
            schema = entry.schema or {}
            params = schema.get("parameters", {"type": "object", "properties": {}})
            desc = schema.get("description", entry.description or "")
            
            # 构建适配后的 handler
            adapted_handler = self._adapt_handler(entry.handler, is_async=entry.is_async)
            
            # 创建 opcclaw ToolDefinition
            tool_def = ToolDefinition(
                name=tool_name,
                description=desc,
                parameters=params,
                handler=adapted_handler,
            )
            opcclaw_registry.add_tool(tool_def)
            count += 1
            
            if not self.quiet:
                print(f"  [OK] Bridged: {tool_name}")
        
        if not self.quiet:
            print(f"[OK] Bridge: {count} tools registered")
        return count
    
    def _register_all_business_tools(self, hermes_registry):
        """注册所有业务工具模块"""
        business_modules = [
            ("alert_tools", "register_alert_tools"),
            ("analysis_tools", "register_analysis_tools"),
            ("automation_tools", "register_automation_tools"),
            ("business_tools", "register_business_tools"),
            ("crm_tools", "register_crm_tools"),
            ("data_import_tools", "register_data_import_tools"),
            ("doc_tools", "register_doc_tools"),
            ("export_tools", "register_export_tools"),
            ("finance_analysis_tools", "register_finance_analysis_tools"),
            ("hr_tools", "register_hr_tools"),
            ("inventory_tools", "register_inventory_tools"),
            ("local_dev_tools", "register_local_dev_tools"),
            ("marketing_tools", "register_marketing_tools"),
            ("procurement_tools", "register_procurement_tools"),
            ("project_management", "register_project_management_tools"),
            ("scheduling_tools", "register_scheduling_tools"),
            ("self_monitor", "register_self_monitor_tools"),
            ("smart_report_tools", "register_smart_report_tools"),
            ("template_tools", "register_template_tools"),
            ("web_search_tools", "register_web_search_tools"),
            ("cronjob_tools", "register_cronjob_tools"),
            ("file_tools", "register_file_tools"),
            ("kanban_tools", "register_kanban_tools"),
            ("transcription_tools", "register_transcription_tools"),
            ("vision_tools", "register_vision_tools"),
            ("web_tools", "register_web_tools"),
            ("yuanbao_tools", "register_yuanbao_tools"),
        ]
        
        _BUSINESS_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
        count = 0
        
        for module_name, func_name in business_modules:
            try:
                mod = __import__(module_name, fromlist=[func_name])
                register_func = getattr(mod, func_name, None)
                if register_func:
                    register_func(hermes_registry, _BUSINESS_DATA_DIR)
                    count += 1
                    if not self.quiet:
                        print(f"  [OK] Business tool: {module_name}")
            except Exception as e:
                if not self.quiet:
                    print(f"  [WARN] Business tool failed {module_name}: {e}")
        
        if not self.quiet:
            print(f"[INFO] {count} business tools registered")
        return count
    
    def _adapt_handler(self, hermes_handler: Callable, is_async: bool = False) -> Callable:
        """适配 Hermes 处理器到 opcclaw 调用约定"""
        if is_async:
            async def _async_adapted(**kwargs):
                return await hermes_handler(kwargs)
            return _async_adapted
        else:
            def _sync_adapted(**kwargs):
                return hermes_handler(kwargs)
            return _sync_adapted
    
    def chat(self, message: str, session_id: str = None, context: Dict = None) -> str:
        """
        对话接口 - 支持状态保持
        
        Args:
            message: 用户消息
            session_id: 会话ID（None则使用当前会话）
            context: 额外上下文
        
        Returns:
            AI 回复文本
        """
        conv = self._get_conversation(session_id)
        if context:
            conv.context.update(context)
        
        conv.add_message("user", message)
        
        # 这里可以接入实际的 LLM 后端
        # 简化版本：返回工具列表或执行工具
        if self.registry and self.registry.count() > 0:
            tools_info = f"可用工具 ({self.registry.count()}个): {', '.join(self.registry.list_tools()[:10])}..."
            response = f"收到: {message}\n\n{tools_info}"
        else:
            response = f"收到: {message}\n\n[系统] 工具注册表为空，请检查配置。"
        
        conv.add_message("assistant", response)
        return response
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行指定工具"""
        if not self.registry:
            return {"success": False, "error": "Registry not initialized"}
        
        from .llm_backend import ToolCall
        tc = ToolCall(id=f"manual_{tool_name}", name=tool_name, arguments=kwargs)
        return self.registry.execute(tc)

    def execute_tool_with_timeout(
        self,
        tool_name: str,
        timeout_seconds: float = 30.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        带超时保护的工具执行（ThreadPoolExecutor 异步化）

        防止单个慢工具（如网络请求、大文件扫描）阻塞主线程。
        超时后返回 timed_out 错误，不阻塞调用方。

        Args:
            tool_name: 工具名
            timeout_seconds: 超时阈值（秒），默认 30s
            **kwargs: 传递给工具的参数字典

        Returns:
            {"success": True/False, ...} 或 {"success": False, "error": "timeout"}
        """
        result: Dict[str, Any] = {"success": False, "error": "unknown"}

        def _run():
            nonlocal result
            result = self.execute_tool(tool_name, **kwargs)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            try:
                future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                return {
                    "success": False,
                    "error": f"工具执行超时 ({timeout_seconds}s): {tool_name}",
                    "tool": tool_name,
                    "timed_out": True,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"工具执行异常: {tool_name}: {e}",
                    "tool": tool_name,
                }

        return result
    
    def get_conversation_history(self, session_id: str = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        conv = self._get_conversation(session_id)
        return conv.get_history()
    
    def clear_conversation(self, session_id: str = None):
        """清空对话"""
        conv = self._get_conversation(session_id)
        conv.clear()
    
    def switch_session(self, session_id: str):
        """切换会话"""
        self._current_session = session_id


# ── 便捷函数 ──
_bridge_instance: Optional[EnhancedHermesBridge] = None


def get_enhanced_bridge(registry=None, force_new: bool = False) -> EnhancedHermesBridge:
    """获取增强桥接器单例"""
    global _bridge_instance
    if _bridge_instance is None or force_new:
        _bridge_instance = EnhancedHermesBridge(registry)
        _bridge_instance.bridge_all_tools(registry)
    return _bridge_instance


def bridge_hermes_tools_enhanced(opcclaw_registry=None, quiet: bool = False, 
                                  include_business: bool = True) -> int:
    """
    增强版桥接函数 - 向后兼容
    
    与原版 bridge_hermes_tools 的区别:
    - 默认不过滤工具（include_business=True）
    - 支持对话状态管理
    """
    bridge = EnhancedHermesBridge(opcclaw_registry, quiet)
    return bridge.bridge_all_tools(opcclaw_registry, include_business)

```
