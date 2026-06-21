# `iqra/iqra_cli/cli.py`

> 路径：`iqra/iqra_cli/cli.py` | 行数：194


---


```python
#!/usr/bin/env python3
"""
iqra_cli.cli — Iqra 命令行对话入口

用法:
  iqra chat                     交互式对话
  iqra chat -m "分析这个文件"    单次对话
  iqra chat --model qwen2.5:7b  指定模型
  iqra chat --session work      指定会话
  iqra memory list|add|search   记忆管理
  iqra tools list               列出可用工具
"""

import argparse
import sys
import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _get_iqra_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_path() -> None:
    # 需要把 iqra 的父目录加入 sys.path，
    # 让 iqra 作为包被正确解析（from iqra.core.xxx 等导入）
    iqra_root = str(_get_iqra_root())
    parent = os.path.dirname(iqra_root)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    if iqra_root not in sys.path:
        sys.path.insert(0, iqra_root)


def _build_chat_engine(model: str = None, session_id: str = "default"):
    """构建 ChatEngine 实例。"""
    _ensure_path()
    from core.llm_backend import create_backend
    from core.chat_engine import ChatEngine
    from core.tool_registry import ToolRegistry

    if model is None:
        from core.core_engine import _get_default_model
        model = _get_default_model()
    backend = create_backend("ollama", model=model)

    registry = ToolRegistry()
    engine = ChatEngine(backend=backend, registry=registry, session_id=session_id)
    return engine


def cmd_chat(args) -> None:
    """对话命令入口。"""
    engine = _build_chat_engine(model=args.model, session_id=args.session)

    if args.message:
        # 单次对话
        reply = engine.chat(args.message)
        print(reply)
        return

    # 交互式对话
    print(f"Iqra 交互式对话 (模型: {engine.backend.config.model if hasattr(engine.backend, 'config') else 'ollama'}, 会话: {engine.session_id})")
    print("输入消息后回车发送，输入 /exit 退出，输入 /clear 清空上下文\n")

    try:
        while True:
            user_input = input("> ").strip()
            if not user_input:
                continue
            if user_input == "/exit":
                print("再见。")
                break
            if user_input == "/clear":
                engine.reset()
                print("[上下文已清空]")
                continue
            if user_input == "/history":
                msgs = engine.get_history()
                for i, m in enumerate(msgs):
                    role = m.get("role", "?")
                    content = m.get("content", "")
                    if isinstance(content, str) and len(content) > 120:
                        content = content[:120] + "..."
                    print(f"  [{i}] {role}: {content}")
                continue

            reply = engine.chat(user_input)
            print(f"\n{reply}\n")

    except (KeyboardInterrupt, EOFError):
        print("\n再见。")


def cmd_memory(args) -> None:
    """记忆管理命令。"""
    _ensure_path()
    from core.smart_memory_adapter import SmartMemoryStore

    store = SmartMemoryStore()

    if args.memory_action == "list":
        providers = store.list_providers() if hasattr(store, "list_providers") else []
        print(f"已加载 {len(providers)} 个记忆插件:")
        for p in providers:
            print(f"  - {p}")

    elif args.memory_action == "search":
        query = args.query
        if not query:
            print("请提供搜索关键词: iqra memory search <关键词>")
            return
        results = store.search(query) if hasattr(store, "search") else []
        print(f"搜索 '{query}' 结果 ({len(results)} 条):")
        for r in results[:10]:
            print(f"  - {r}")

    elif args.memory_action == "add":
        text = args.text
        if not text:
            print("请提供记忆内容: iqra memory add <内容>")
            return
        store.add(text) if hasattr(store, "add") else print("记忆写入接口不可用")
        print(f"已添加记忆: {text}")


def cmd_tools(args) -> None:
    """工具列表命令。"""
    _ensure_path()
    try:
        from toolsets import TOOLSETS, initialize
        initialize()
        if TOOLSETS:
            print(f"可用工具 ({len(TOOLSETS)} 个):")
            for name, info in sorted(TOOLSETS.items()):
                desc = info.get("description", "")
                toolset = info.get("toolset", "?")
                print(f"  {name} [{toolset}] — {desc}")
        else:
            print("工具注册表为空。")
    except ImportError:
        print("工具模块未找到。")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Iqra 命令行入口",
        prog="iqra",
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    # ── chat ──
    chat_p = sub.add_parser("chat", help="对话")
    chat_p.add_argument("-m", "--message", type=str, default=None, help="单次对话消息")
    chat_p.add_argument("--model", type=str, default=None, help="指定模型（默认从配置读取）")
    chat_p.add_argument("--session", type=str, default="default", help="会话 ID")
    chat_p.set_defaults(func=cmd_chat)

    # ── memory ──
    mem_p = sub.add_parser("memory", help="记忆管理")
    mem_s = mem_p.add_subparsers(dest="memory_action", help="操作")

    mem_list = mem_s.add_parser("list", help="列出记忆插件")
    mem_list.set_defaults(func=cmd_memory)

    mem_search = mem_s.add_parser("search", help="搜索记忆")
    mem_search.add_argument("query", type=str, help="搜索关键词")
    mem_search.set_defaults(func=cmd_memory)

    mem_add = mem_s.add_parser("add", help="添加记忆")
    mem_add.add_argument("text", type=str, help="记忆内容")
    mem_add.set_defaults(func=cmd_memory)

    # ── tools ──
    tools_p = sub.add_parser("tools", help="工具管理")
    tools_s = tools_p.add_subparsers(dest="tools_action", help="操作")

    tools_list = tools_s.add_parser("list", help="列出可用工具")
    tools_list.set_defaults(func=cmd_tools)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()

```
