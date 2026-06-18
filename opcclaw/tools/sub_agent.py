# -*- coding: utf-8 -*-
"""
MiniAgent -- 轻量同步子Agent执行器

为主 AgentLoop 提供多Agent协作能力。当任务可以按领域拆解时，
主Agent可以派发子任务给专注某一领域的MiniAgent同步执行，
子Agent完成后将结果回传给主Agent继续推进。

设计原则：
- 非 QObject，避免递归信号问题
- 复用父 Agent 的 LLM backend 和工具注册表
- 同步执行，主Agent阻塞等待结果
- 独立的 messages 列表 + 专用 system prompt
- 最大执行轮数可配置（默认10轮）
"""

import json
import enum
import logging
from typing import Optional, Dict, Any, List, Callable

logger = logging.getLogger(__name__)


class SubAgentType(enum.Enum):
    """子Agent专业领域类型"""

    FILE = "file_agent"
    CODE = "code_agent"
    SYSTEM = "system_agent"
    RESEARCH = "research_agent"
    GENERAL = "general_agent"


# ── 各领域专用系统提示词 ──

SUB_AGENT_PROMPTS: Dict[SubAgentType, str] = {
    SubAgentType.FILE: """你是一个文件操作专家子Agent，专注于文件系统任务。

## 核心能力
- 搜索文件：按名称、内容、类型、日期搜索整个文件系统
- 读取文件：读取文本、代码、配置文件内容
- 写入文件：创建或覆写文件
- 编辑文件：精确修改文件中的特定内容
- 文件整理：按规则归类、重命名、移动文件
- 格式转换：文件格式间转换
- 文件分析：总结、统计、提取关键信息

## 工具选择铁律
- 读文件 → 只用 read_file，严禁 execute_shell + cat/osascript
- 搜文件 → 只用 search_files，严禁 find/grep/mdfind
- 写文件 → 只用 write_file/edit_file，严禁 echo/重定向
- 列目录 → 只用 list_directory，严禁 ls

## 执行原则
- 先用搜索工具定位目标文件，不要猜测路径
- 独立操作（如同时读多个文件）并行调用
- 任务完成立即停止，不要追加验证性重新搜索
- 完成后明确列出操作了哪些文件（绝对路径）
- 遇到权限问题或路径不存在时，如实报告""",

    SubAgentType.CODE: """你是一个代码专家子Agent，专注于软件开发任务。

## 核心能力
- 编写代码：生成完整的、可运行的代码文件
- 修改代码：精确编辑已有代码，只改必要部分
- 调试定位：阅读代码找出bug，分析根因
- 代码搜索：搜索函数定义、类引用、导入关系
- 运行测试：执行单元测试、集成测试
- Git操作：查看状态、差异、提交历史
- 依赖管理：安装包、更新配置

## 执行原则
- 修改前先读懂现有代码结构
- 最小改动原则：只改需要改的地方
- 修改后运行相关测试验证
- 代码风格与项目现有风格保持一致""",

    SubAgentType.SYSTEM: """你是一个系统操作专家子Agent，专注于macOS系统任务。

## 核心能力
- 系统信息查询：硬件配置、系统版本、磁盘空间、内存使用
- 进程管理：查看运行进程、终止进程
- 系统配置：读写macOS偏好设置（defaults）
- 文件系统操作：创建/删除/移动文件目录
- 网络诊断：ping、端口检查、网络状态
- 安装管理：brew安装/卸载软件包

## 执行原则
- 破坏性操作（删除、终止进程、修改系统配置）必须先确认影响范围
- 尽量使用可逆操作
- 系统目录（/System, /Library）只读不写""",

    SubAgentType.RESEARCH: """你是一个信息研究专家子Agent，专注于信息搜集与分析任务。

## 核心能力
- 网页搜索：使用搜索引擎查找信息
- 网页抓取：读取指定URL的完整内容
- 信息提取：从网页内容中提取关键数据和结构化信息
- 对比分析：对比多个来源的信息，找出异同
- 总结归纳：将多篇内容提炼为核心要点
- 时效性验证：确认信息的最新更新时间

## 执行原则
- 优先使用多个信息源交叉验证
- 区分事实和观点
- 标注信息来源（URL）
- 信息不足时如实说明，不要编造""",

    SubAgentType.GENERAL: """你是一个通用任务子Agent，可以处理不特定领域的任务。

## 核心能力
- 综合分析：结合多种工具解决跨领域问题
- 任务拆解：将复杂任务分解为可执行的步骤
- 结果汇总：整理多步操作的结果为清晰报告

## 执行原则
- 根据任务性质选择合适的工具
- 保持操作简洁高效
- 完成后给出清晰的总结""",
}


class MiniAgent:
    """轻量同步子Agent执行器

    不是QObject，避免与AgentLoop的QThread产生递归依赖。
    在主Agent的线程中同步执行，复用backend和registry。

    用法:
        mini = MiniAgent(backend, registry, SubAgentType.FILE)
        result = mini.run("搜索桌面上所有的PDF文件")
        # result: {"success": True, "summary": "...", "files": [...], "iterations": 3}
    """

    DEFAULT_MAX_ROUNDS = 10
    DEFAULT_TASK_TIMEOUT = 120  # 子任务最长执行秒数

    def __init__(
        self,
        backend,
        registry,
        sub_type: SubAgentType = SubAgentType.GENERAL,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
        timeout: int = DEFAULT_TASK_TIMEOUT,
        on_progress: Optional[Callable[[str], None]] = None,
    ):
        """
        Args:
            backend: LLM backend 实例（复用父Agent的）
            registry: ToolRegistry 实例（复用父Agent的）
            sub_type: 子Agent专业类型
            max_rounds: 最大执行轮数
            timeout: 最长执行秒数
            on_progress: 进度回调 (status_message) -> None
        """
        self._backend = backend
        self._registry = registry
        self._sub_type = sub_type
        self._max_rounds = max_rounds
        self._timeout = timeout
        self._on_progress = on_progress

    def run(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """执行子任务并返回结构化结果

        Args:
            task: 子任务描述
            context: 可选的上下文信息（父Agent已获取的数据）

        Returns:
            {
                "success": bool,
                "summary": str,        # 任务总结
                "files": list[str],    # 涉及的文件路径
                "iterations": int,     # 实际执行轮数
                "error": str,          # 失败时的错误信息
                "raw_output": str,     # 原始输出
            }
        """
        import time

        start_time = time.monotonic()

        # 构建专用的 messages 列表
        system_prompt = self._build_system_prompt(task, context)
        messages = [{"role": "system", "content": system_prompt}]

        user_msg = f"请完成以下任务：\n\n{task}"
        if context:
            user_msg = f"背景信息：\n{context}\n\n任务：\n{task}"
        messages.append({"role": "user", "content": user_msg})

        tools = self._registry.to_openai_tools() if self._registry.count() > 0 else None

        final_output = ""
        iteration = 0
        files_touched: List[str] = []

        try:
            for iteration in range(1, self._max_rounds + 1):
                # 超时检查
                if time.monotonic() - start_time > self._timeout:
                    return {
                        "success": False,
                        "summary": "",
                        "files": files_touched,
                        "iterations": iteration,
                        "error": f"子任务超时（>{self._timeout}s）",
                        "raw_output": final_output,
                    }

                if self._on_progress:
                    self._on_progress(f"子Agent[{self._sub_type.value}] 第{iteration}轮...")

                # 调用 LLM
                try:
                    response = self._backend.chat(messages, tools)
                except Exception as e:
                    logger.error(f"MiniAgent LLM call failed (round {iteration}): {e}")
                    return {
                        "success": False,
                        "summary": "",
                        "files": files_touched,
                        "iterations": iteration,
                        "error": f"LLM调用失败: {e}",
                        "raw_output": final_output,
                    }

                # 没有工具调用 → 任务完成
                if not response.tool_calls:
                    final_output = response.content or ""
                    messages.append({"role": "assistant", "content": final_output})
                    break

                # 执行工具调用
                assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
                for tc in response.tool_calls:
                    if self._on_progress:
                        self._on_progress(f"  调用工具: {tc.name}")

                    try:
                        result = self._registry.execute(tc)
                    except Exception as e:
                        logger.error(f"MiniAgent tool failed {tc.name}: {e}")
                        result = {"success": False, "error": str(e)}

                    # 记录涉及的文件
                    self._extract_files_from_tool(tc, result, files_touched)

                    # 构建 tool_call 和 tool 消息
                    try:
                        assistant_msg["tool_calls"].append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                            },
                        })
                    except (TypeError, ValueError):
                        continue

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                    messages.append(tool_msg)

                messages.append(assistant_msg)

            else:
                # 达到最大轮数
                final_output = "子任务达到最大执行轮数，未完成。"
                messages.append({"role": "assistant", "content": final_output})

        except Exception as e:
            logger.error(f"MiniAgent execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "summary": "",
                "files": files_touched,
                "iterations": iteration,
                "error": str(e),
                "raw_output": final_output,
            }

        return {
            "success": True,
            "summary": final_output,
            "files": files_touched,
            "iterations": iteration,
            "error": "",
            "raw_output": final_output,
        }

    def _build_system_prompt(self, task: str, context: Optional[str]) -> str:
        """构建子Agent专用的系统提示词"""
        base = SUB_AGENT_PROMPTS.get(self._sub_type, SUB_AGENT_PROMPTS[SubAgentType.GENERAL])

        parts = [base]

        # 添加 macOS 环境信息
        parts.append("""
## 运行环境
- 操作系统: macOS 26
- 用户主目录: /Users/opc
- 桌面路径: /Users/opc/Desktop
- 下载目录: /Users/opc/Downloads
- 文档目录: /Users/opc/Documents
- 项目根目录: /Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic/

## 输出要求
- 完成后用简洁的中文总结结果
- 涉及文件时给出绝对路径
- 如果任务无法完成，说明原因和建议
""")

        return "\n".join(parts)

    def _extract_files_from_tool(
        self,
        tc,
        result: dict,
        files_touched: List[str],
    ) -> None:
        """从工具调用结果中提取涉及的文件路径"""
        name = tc.name.lower()
        args = tc.arguments if isinstance(tc.arguments, dict) else {}

        # 提取文件路径参数
        path_keys = ["path", "file_path", "source", "dest", "target", "output"]
        for key in path_keys:
            val = args.get(key)
            if isinstance(val, str) and val.startswith("/"):
                if val not in files_touched:
                    files_touched.append(val)

        # write_file / edit_file / save 类工具的结果中可能包含路径
        if isinstance(result, dict):
            for key in ["path", "file_path", "saved_to"]:
                val = result.get(key)
                if isinstance(val, str) and val.startswith("/"):
                    if val not in files_touched:
                        files_touched.append(val)
