# -*- coding: utf-8 -*-
"""
AgentLoop — 自主 Agent 执行循环 (对标 Codex / Claude Code)

在 ChatEngine 的工具调用循环之上叠加 Think → Plan → Act → Observe → Reflect
自主执行模式，支持多步推理、错误恢复、进度追踪和可中断执行。

与 ChatEngine 的关系：
  - AgentLoop 是 ChatEngine 的上层封装，复用其工具注册表和 LLM 后端
  - AgentLoop 可直接替换 ChatEngine 用于需要自主多步执行的场景
  - ChatEngine 保留用于简单单轮问答

用法:
    from opcclaw.core.agent_loop import AgentLoop
    from opcclaw.core.chat_engine import ChatEngine

    engine = ChatEngine(backend=..., registry=..., ...)
    agent = AgentLoop(engine)

    # 同步执行
    result = agent.run("帮我重构 src/ 下所有 Python 文件的 import 语句")

    # 流式执行
    for event in agent.run_stream("排查为什么 API 返回 500"):
        print(event)

    # 取消执行
    agent.cancel()

特性:
  - Think-Plan-Act-Observe-Reflect 五阶段 ReAct 循环
  - 自动错误恢复（最多 3 次重试，每次尝试不同策略）
  - 进度事件流（每一步都有回调）
  - 可中断（cancel() 方法）
  - 可配置最大迭代、超时
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Iterator, Callable, List, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal

from .chat_engine import ChatEngine
from .opcclaw_logging import logger


# ═══════════════════════════════════════════
# 事件类型
# ═══════════════════════════════════════════

class AgentEventType(Enum):
    THINK = auto()       # 分析需求
    PLAN = auto()        # 生成计划
    ACT = auto()         # 执行工具
    OBSERVE = auto()     # 观察结果
    REFLECT = auto()     # 反思调整
    COMPLETE = auto()    # 任务完成
    ERROR = auto()       # 错误
    CANCELLED = auto()   # 被取消
    PROGRESS = auto()    # 进度更新


@dataclass
class AgentEvent:
    """Agent 执行过程中的事件"""
    type: AgentEventType
    step: int = 0                     # 当前步数
    total_steps: int = 0              # 预计总步数（PLAN 时设定）
    message: str = ""                 # 事件描述
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    summary: str                      # 自然语言总结
    steps_taken: int                  # 实际执行步数
    tools_called: List[str]           # 调用过的工具名列表
    errors: List[str]                 # 遇到的错误
    events: List[AgentEvent]          # 完整事件日志
    duration_seconds: float           # 执行耗时


# ═══════════════════════════════════════════
# Agent 系统提示词
# ═══════════════════════════════════════════

AGENT_SYSTEM_PROMPT = """你是一个自主 AI Agent，能够独立完成复杂的多步骤任务。

## 执行模式：Think → Plan → Act → Observe → Reflect

每次收到任务时，按以下流程执行：

1. **THINK（分析）**：仔细理解用户需求。需要哪些信息？可能遇到什么障碍？
2. **PLAN（规划）**：将任务拆解为具体的、有序的步骤。每个步骤应该是可独立执行的原子操作。
3. **ACT（执行）**：一次执行一个步骤，调用合适的工具。每次只做一个操作。
4. **OBSERVE（观察）**：仔细检查工具返回的结果。成功了吗？得到了什么？
5. **REFLECT（反思）**：任务是否完成？如果没有，根据当前状态调整计划，然后继续 ACT。

## 核心规则

- **一次只做一件事**：每次工具调用只完成一个步骤，不要试图一次调用做多个不相关的操作。
- **出错不放弃**：遇到错误时，分析原因并尝试替代方案。同一个操作最多尝试 3 种不同方法。
- **确认后继续**：关键操作（删除、覆盖、修改系统配置）执行前要基于已有信息判断安全性。
- **完成后总结**：任务全部完成后，用简洁的中文总结完成了什么、结果如何。
- **主动搜索**：需要文件路径或代码上下文时，先用搜索工具查找，不要猜测。
- **保持上下文**：利用工具返回的结果推进后续步骤，不要重复已完成的查询。

## 示例执行流程

用户: "把 src/utils.py 里的所有 print 改成 logger.info"

THINK: 需要先读取文件内容，找到所有 print 语句，替换为 logger.info，然后保存。
PLAN: ① 读取 src/utils.py  ② 找到所有 print 语句  ③ 替换为 logger.info  ④ 保存文件

ACT → read_file("src/utils.py")
OBSERVE → 文件共 200 行，找到 5 处 print
ACT → edit_file 替换第 1 处 print
OBSERVE → 第 1 处替换成功
... (继续替换其余 4 处)
REFLECT → 全部 5 处替换完成，文件已保存
COMPLETE → "已将 src/utils.py 中的 5 处 print 替换为 logger.info"

## 可用工具

你可以使用系统中注册的所有工具。每个工具调用的结果会立即反馈给你。
如果不确定工具的参数格式，先用简单参数测试一下。

## macOS 环境

- 操作系统: macOS 26, Apple M5
- 用户主目录: `/Users/opc`
- 桌面路径: `/Users/opc/Desktop`
- 下载目录: `/Users/opc/Downloads`
- 文档目录: `/Users/opc/Documents`
- 项目根目录: `/Volumes/D盘工作区/一人公司/one_company_cosmic/`
- 常用应用: 终端(`/System/Applications/Utilities/Terminal.app`)、访达(Finder)、Safari、系统设置
- 所有文件操作默认基于以上路径，用户说"桌面"即指 `/Users/opc/Desktop`"""


# ═══════════════════════════════════════════
# AgentLoop 主类
# ═══════════════════════════════════════════

class AgentLoop(QObject):
    """
    自主 Agent 执行循环

    信号:
      on_event: 每一步发出事件（THINK/PLAN/ACT/OBSERVE/REFLECT/COMPLETE/ERROR/CANCELLED）
      on_progress: 进度百分比更新 (0-100)
      on_tool_start: 工具开始执行（兼容 ChatEngine 信号）
      on_tool_result: 工具执行结果（兼容 ChatEngine 信号）
    """

    on_event = pyqtSignal(AgentEvent)
    on_progress = pyqtSignal(int)
    on_tool_start = pyqtSignal(str, dict)
    on_tool_result = pyqtSignal(str, bool, str)

    # 默认配置
    DEFAULT_MAX_ITERATIONS = 50
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_TIMEOUT_SECONDS = 300  # 5 分钟

    def __init__(
        self,
        engine: ChatEngine,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        verbose: bool = True,
    ):
        """
        Args:
            engine: ChatEngine 实例（已配置后端和工具）
            max_iterations: 最大迭代次数（超过后强制终止）
            max_retries: 单个操作的最大重试次数
            timeout_seconds: 总执行超时（秒）
            verbose: 是否发出详细事件
        """
        super().__init__()
        self._engine = engine
        self._max_iterations = max_iterations
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._verbose = verbose

        self._cancelled = False
        self._events: List[AgentEvent] = []
        self._tools_called: List[str] = []
        self._errors: List[str] = []
        self._start_time: float = 0.0
        self._current_step = 0
        self._total_steps = 0

        # 保存原始 system prompt，以便注入 Agent 指令后恢复
        self._original_system_prompt = ""

        # 转发内部 engine 的信号到 AgentLoop 自身信号
        self._engine.on_tool_start.connect(self.on_tool_start.emit)
        self._engine.on_tool_result.connect(self.on_tool_result.emit)

    # ── 公开接口 ──

    def run(self, user_message: str) -> AgentResult:
        """
        同步执行任务

        Args:
            user_message: 用户的任务描述

        Returns:
            AgentResult: 包含成功状态、总结、事件日志等
        """
        self._reset()
        self._start_time = time.time()

        try:
            self._inject_agent_prompt()
            result = self._execute_loop(user_message)
        finally:
            self._restore_system_prompt()

        elapsed = time.time() - self._start_time
        return AgentResult(
            success=result.get("success", False),
            summary=result.get("summary", ""),
            steps_taken=self._current_step,
            tools_called=self._tools_called,
            errors=self._errors,
            events=self._events,
            duration_seconds=elapsed,
        )

    def run_stream(self, user_message: str) -> Iterator[AgentEvent]:
        """
        流式执行任务（生成器），每步 yield 事件

        Usage:
            for event in agent.run_stream("排查 API 报错"):
                if event.type == AgentEventType.COMPLETE:
                    print(event.message)
        """
        self._reset()
        self._start_time = time.time()

        try:
            self._inject_agent_prompt()
            for event in self._execute_loop_stream(user_message):
                yield event
        finally:
            self._restore_system_prompt()

    def cancel(self) -> None:
        """取消当前执行"""
        self._cancelled = True
        event = AgentEvent(
            type=AgentEventType.CANCELLED,
            step=self._current_step,
            message="执行已被用户取消",
        )
        self._events.append(event)
        self.on_event.emit(event)
        logger.info("AgentLoop 被用户取消")

    # ── 内部方法 ──

    def _reset(self) -> None:
        self._cancelled = False
        self._events = []
        self._tools_called = []
        self._errors = []
        self._current_step = 0
        self._total_steps = 0

    def _inject_agent_prompt(self) -> None:
        """注入 Agent 系统提示词到 engine 的消息列表头部"""
        msgs = self._engine.messages
        self._original_system_prompt = ""

        # 替换已有的 system 消息（如果存在）为 Agent 增强版
        for i, msg in enumerate(msgs):
            if msg.get("role") == "system":
                self._original_system_prompt = msg["content"]
                msgs[i] = {
                    "role": "system",
                    "content": self._original_system_prompt + "\n\n" + AGENT_SYSTEM_PROMPT,
                }
                return

        # 没有 system 消息，插入到头部
        msgs.insert(0, {"role": "system", "content": AGENT_SYSTEM_PROMPT})

    def _restore_system_prompt(self) -> None:
        """恢复原始 system prompt"""
        msgs = self._engine.messages
        if not msgs or msgs[0].get("role") != "system":
            return

        if self._original_system_prompt:
            msgs[0]["content"] = self._original_system_prompt
        else:
            # 没有原始 prompt，说明是我们新插入的 → 移除
            msgs.pop(0)

    def _emit(self, event_type: AgentEventType, message: str, data: dict = None) -> None:
        """发出事件"""
        event = AgentEvent(
            type=event_type,
            step=self._current_step,
            total_steps=self._total_steps,
            message=message,
            data=data or {},
        )
        self._events.append(event)
        if self._verbose:
            self.on_event.emit(event)

        # 进度估算
        if self._total_steps > 0:
            progress = min(int(self._current_step / self._total_steps * 100), 99)
            self.on_progress.emit(progress)

    def _check_timeout(self) -> bool:
        """检查是否超时"""
        if self._timeout_seconds <= 0:
            return False
        elapsed = time.time() - self._start_time
        return elapsed > self._timeout_seconds

    def _execute_loop(self, user_message: str) -> dict:
        """核心执行循环（同步版）"""
        # 先让 LLM 分析并生成计划（单轮）
        self._emit(AgentEventType.THINK, f"分析任务: {user_message[:100]}...")

        # 直接将用户消息发给 engine（engine 会自动追加到 messages）
        response = self._engine.backend.chat(
            self._engine.messages + [{"role": "user", "content": user_message}],
            self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None,
        )

        # 处理首轮响应
        if response.content and not response.tool_calls:
            # LLM 直接给出文本回复 → 简单任务，无需多步
            self._current_step = 1
            self._emit(AgentEventType.COMPLETE, response.content)
            self.on_progress.emit(100)
            return {"success": True, "summary": response.content}

        # 有工具调用 → 进入多步循环
        self._total_steps = self._max_iterations
        self._emit(AgentEventType.PLAN, f"开始执行，最多 {self._max_iterations} 步")

        return self._tool_loop(user_message)

    def _execute_loop_stream(self, user_message: str) -> Iterator[AgentEvent]:
        """核心执行循环（流式版）"""
        event = AgentEvent(AgentEventType.THINK, 0, 0, f"分析任务: {user_message[:100]}...")
        self._events.append(event)
        yield event

        response = self._engine.backend.chat(
            self._engine.messages + [{"role": "user", "content": user_message}],
            self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None,
        )

        if response.content and not response.tool_calls:
            self._current_step = 1
            event = AgentEvent(AgentEventType.COMPLETE, 1, 1, response.content)
            self._events.append(event)
            yield event
            yield from []  # end generator
            return

        self._total_steps = self._max_iterations
        event = AgentEvent(AgentEventType.PLAN, 0, self._max_iterations,
                          f"开始执行，最多 {self._max_iterations} 步")
        self._events.append(event)
        yield event

        yield from self._tool_loop_stream(user_message)

    def _tool_loop(self, user_message: str) -> dict:
        """工具调用循环（同步版）"""
        # 使用 engine 的 chat 方法（它会自动处理多轮工具调用）
        # 但我们需要在每一轮之间插入观察和反思
        self._engine.messages.append({"role": "user", "content": user_message})
        self._engine._trim_context()

        tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

        for iteration in range(self._max_iterations):
            if self._cancelled:
                return {"success": False, "summary": "执行被取消"}

            if self._check_timeout():
                self._emit(AgentEventType.ERROR, f"执行超时（{self._timeout_seconds} 秒）")
                return {"success": False, "summary": f"超时: 已执行 {self._current_step} 步"}

            self._current_step = iteration + 1

            # ACT 阶段
            try:
                response = self._engine.backend.chat(self._engine.messages, tools)
            except Exception as e:
                error_msg = f"LLM 调用失败: {e}"
                self._errors.append(error_msg)
                self._emit(AgentEventType.ERROR, error_msg)
                # 尝试重试
                if iteration < self._max_retries:
                    time.sleep(1)
                    continue
                return {"success": False, "summary": error_msg}

            # 无工具调用 → 任务完成
            if not response.tool_calls:
                content = response.content or ""
                self._engine.messages.append({"role": "assistant", "content": content})
                self._emit(AgentEventType.REFLECT, "任务完成")
                self._emit(AgentEventType.COMPLETE, content)
                self.on_progress.emit(100)
                return {"success": True, "summary": content}

            # 处理工具调用
            assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
            for tc in response.tool_calls:
                self._tools_called.append(tc.name)
                tool_data = {"tool": tc.name, "args": tc.arguments}
                self._emit(AgentEventType.ACT, f"调用工具: {tc.name}", tool_data)

                # 执行工具
                retry_count = 0
                while retry_count <= self._max_retries:
                    try:
                        self._engine.on_tool_start.emit(tc.name, tc.arguments)
                        result = self._engine.registry.execute(tc)
                        self._engine.on_tool_result.emit(
                            tc.name, result.get("success", False),
                            str(result.get("result", result.get("error", "")))[:200],
                        )
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count > self._max_retries:
                            error_msg = f"工具 {tc.name} 执行失败（已重试 {self._max_retries} 次）: {e}"
                            self._errors.append(error_msg)
                            result = {"success": False, "error": error_msg}
                            self._emit(AgentEventType.ERROR, error_msg)
                            break
                        self._emit(AgentEventType.OBSERVE,
                                  f"{tc.name} 失败，重试 {retry_count}/{self._max_retries}: {e}")
                        time.sleep(0.5)

                # OBSERVE 阶段
                success = result.get("success", False)
                output = str(result.get("result", result.get("error", "")))[:500]
                self._emit(AgentEventType.OBSERVE,
                          f"{'✅' if success else '❌'} {tc.name}: {output[:200]}",
                          {"tool": tc.name, "success": success, "output": output})

                # 构建 assistant 消息
                assistant_msg["tool_calls"].append({
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                })

                # 构建 tool 结果消息
                self._engine.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

            self._engine.messages.append(assistant_msg)

        # 达到最大迭代
        self._emit(AgentEventType.ERROR,
                  f"达到最大迭代次数 {self._max_iterations}，任务可能未完成")
        return {"success": False,
                "summary": f"达到最大迭代次数 ({self._max_iterations} 步)。"
                          f"已调用工具: {', '.join(self._tools_called)}"}

    def _tool_loop_stream(self, user_message: str) -> Iterator[AgentEvent]:
        """工具调用循环（流式版）"""
        self._engine.messages.append({"role": "user", "content": user_message})
        self._engine._trim_context()

        tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

        for iteration in range(self._max_iterations):
            if self._cancelled:
                event = AgentEvent(AgentEventType.CANCELLED, self._current_step, self._total_steps, "执行被取消")
                self._events.append(event)
                yield event
                return

            if self._check_timeout():
                event = AgentEvent(AgentEventType.ERROR, self._current_step, self._total_steps,
                                  f"执行超时（{self._timeout_seconds} 秒）")
                self._events.append(event)
                yield event
                return

            self._current_step = iteration + 1

            try:
                response = self._engine.backend.chat(self._engine.messages, tools)
            except Exception as e:
                error_msg = f"LLM 调用失败: {e}"
                self._errors.append(error_msg)
                event = AgentEvent(AgentEventType.ERROR, self._current_step, self._total_steps, error_msg)
                self._events.append(event)
                yield event
                if iteration < self._max_retries:
                    time.sleep(1)
                    continue
                return

            if not response.tool_calls:
                content = response.content or ""
                self._engine.messages.append({"role": "assistant", "content": content})
                event = AgentEvent(AgentEventType.REFLECT, self._current_step, self._total_steps, "任务完成")
                self._events.append(event)
                yield event
                event = AgentEvent(AgentEventType.COMPLETE, self._current_step, self._total_steps, content)
                self._events.append(event)
                yield event
                return

            assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
            for tc in response.tool_calls:
                self._tools_called.append(tc.name)
                tool_data = {"tool": tc.name, "args": tc.arguments}
                event = AgentEvent(AgentEventType.ACT, self._current_step, self._total_steps,
                                  f"调用工具: {tc.name}", tool_data)
                self._events.append(event)
                yield event

                retry_count = 0
                while retry_count <= self._max_retries:
                    try:
                        self._engine.on_tool_start.emit(tc.name, tc.arguments)
                        result = self._engine.registry.execute(tc)
                        self._engine.on_tool_result.emit(
                            tc.name, result.get("success", False),
                            str(result.get("result", result.get("error", "")))[:200],
                        )
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count > self._max_retries:
                            error_msg = f"工具 {tc.name} 执行失败: {e}"
                            self._errors.append(error_msg)
                            result = {"success": False, "error": error_msg}
                            event = AgentEvent(AgentEventType.ERROR, self._current_step,
                                             self._total_steps, error_msg)
                            self._events.append(event)
                            yield event
                            break
                        event = AgentEvent(AgentEventType.OBSERVE, self._current_step, self._total_steps,
                                          f"{tc.name} 失败，重试 {retry_count}/{self._max_retries}")
                        self._events.append(event)
                        yield event
                        time.sleep(0.5)

                success = result.get("success", False)
                output = str(result.get("result", result.get("error", "")))[:500]
                event = AgentEvent(AgentEventType.OBSERVE, self._current_step, self._total_steps,
                                  f"{'✅' if success else '❌'} {tc.name}: {output[:200]}",
                                  {"tool": tc.name, "success": success, "output": output})
                self._events.append(event)
                yield event

                assistant_msg["tool_calls"].append({
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                })
                self._engine.messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

            self._engine.messages.append(assistant_msg)

        event = AgentEvent(AgentEventType.ERROR, self._current_step, self._total_steps,
                          f"达到最大迭代次数 {self._max_iterations}")
        self._events.append(event)
        yield event

    # ── ChatEngine 兼容接口 ──

    def chat_stream(self, user_message: str) -> Iterator[str]:
        """
        与 ChatEngine.chat_stream 完全兼容的流式接口。
        ChatWorker 可以直接使用 AgentLoop 替代 ChatEngine。

        Yields:
            str: 每个事件或工具结果的描述字符串
        """
        self._reset()
        self._start_time = time.time()

        try:
            self._inject_agent_prompt()

            # 使用 engine 的 chat_stream 驱动多轮调用
            self._engine.messages.append({"role": "user", "content": user_message})
            self._engine._trim_context()

            tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

            for iteration in range(self._max_iterations):
                if self._cancelled:
                    yield "\n\n[执行已被取消]"
                    return

                if self._check_timeout():
                    yield f"\n\n[执行超时（{self._timeout_seconds} 秒），已执行 {self._current_step} 步]"
                    return

                self._current_step = iteration + 1

                try:
                    response = self._engine.backend.chat(self._engine.messages, tools)
                except Exception as e:
                    error_msg = f"\n\n[LLM 调用失败: {e}]"
                    self._errors.append(error_msg)
                    yield error_msg
                    if iteration < self._max_retries:
                        time.sleep(1)
                        continue
                    return

                # 无工具调用 → 任务完成
                if not response.tool_calls:
                    content = response.content or ""
                    self._engine.messages.append({"role": "assistant", "content": content})
                    yield content
                    return

                # 处理工具调用
                assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
                for tc in response.tool_calls:
                    self._tools_called.append(tc.name)
                    yield f"\n\n🔧 调用工具: {tc.name}..."

                    retry_count = 0
                    while retry_count <= self._max_retries:
                        try:
                            self._engine.on_tool_start.emit(tc.name, tc.arguments)
                            result = self._engine.registry.execute(tc)
                            self._engine.on_tool_result.emit(
                                tc.name, result.get("success", False),
                                str(result.get("result", result.get("error", "")))[:200],
                            )
                            break
                        except Exception as e:
                            retry_count += 1
                            if retry_count > self._max_retries:
                                error_msg = f"  ❌ {tc.name} 失败: {e}"
                                self._errors.append(error_msg)
                                result = {"success": False, "error": str(e)}
                                yield error_msg
                                break
                            yield f"  ⚠️ 重试 {retry_count}/{self._max_retries}..."
                            time.sleep(0.5)

                    success = result.get("success", False)
                    output = str(result.get("result", result.get("error", "")))[:300]
                    yield f"\n{'✅' if success else '❌'} {tc.name}: {output}"

                    assistant_msg["tool_calls"].append({
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.name,
                                    "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    })
                    self._engine.messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

                self._engine.messages.append(assistant_msg)

            yield f"\n\n[达到最大迭代次数 {self._max_iterations}，任务可能未完成]"
        finally:
            self._restore_system_prompt()

    # ── ChatEngine 兼容属性与方法 ──

    @property
    def backend(self):
        """兼容 ChatEngine.backend"""
        return self._engine.backend

    @property
    def messages(self):
        return self._engine.messages

    @messages.setter
    def messages(self, value):
        self._engine.messages = value

    def chat(self, user_message: str) -> str:
        """兼容 ChatEngine.chat（同步版）"""
        result = self.run(user_message)
        return result.summary

    def reset(self) -> None:
        if self._engine:
            self._engine.reset()
        self._current_step = 0

    def save(self) -> bool:
        return self._engine.save() if self._engine else False

    def get_history(self) -> list:
        return self._engine.get_history() if self._engine else []

    def message_count(self) -> int:
        return self._engine.message_count() if self._engine else 0

    def inject_context(self, text: str) -> None:
        if self._engine:
            self._engine.inject_context(text)

    def inject_skill(self, skill_name: str) -> bool:
        return self._engine.inject_skill(skill_name) if self._engine else False

    def refresh_skills(self) -> int:
        return self._engine.refresh_skills() if self._engine else 0

    def inject_relevant_skills(self, user_query: str, max_count: int = 5) -> int:
        return self._engine.inject_relevant_skills(user_query, max_count) if self._engine else 0

    def initialize_session(self) -> None:
        if self._engine:
            self._engine.initialize_session()
