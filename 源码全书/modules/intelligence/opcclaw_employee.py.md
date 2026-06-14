# `modules/intelligence/opcclaw_employee.py`

> 路径：`modules/intelligence/opcclaw_employee.py` | 行数：389


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opcclaw 数字员工 — 每个员工都是完整 opcclaw agent 实例
舰队指挥系统 · 数字员工层
舰长 → 球球(CEO) → 6 名 opcclaw 数字员工

与旧版 digital_employee.py 区别：
- 旧版：DigitalEmployee 是 dataclass + 预设任务池假数据，poll() 随机模拟状态
- 新版：OpcclawEmployee 封装完整 OPCclawEngine，每个员工具备真实 AI 能力
"""
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable
from enum import Enum

# 注入 opcclaw 路径
_OPCCLAW_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'opcclaw')
if _OPCCLAW_ROOT not in sys.path:
    sys.path.insert(0, _OPCCLAW_ROOT)

from opcclaw.core.core_engine import OPCclawCoreEngine as OPCclawEngine
from opcclaw.core.llm_backend import ProviderConfig


# ═══════════ 员工状态枚举 ═══════════

class EmployeeStatus(Enum):
    IDLE = "idle"           # 待命中
    THINKING = "thinking"   # LLM 推理中
    WORKING = "working"     # 工具执行中
    REPORTING = "reporting" # 任务完成，汇报中
    ERROR = "error"         # 出错


# ═══════════ 消息类型枚举 ═══════════

class ChatType(Enum):
    ASSIGN = "assign"                # 球球派活
    REPORT = "report"                # 员工汇报
    QUERY = "query"                  # 员工请示
    CAPTAIN_ORDER = "captain_order"  # 舰长下令
    DISPATCH = "dispatch"            # 球球拆解调度
    CAPTAIN_REPORT = "captain_report"  # 球球向舰长汇报
    RESULT = "result"                # 员工任务完成结果


# ═══════════ 数据类 ═══════════

@dataclass
class ChatLog:
    sender: str
    receiver: str
    content: str
    timestamp: float
    msg_type: ChatType


# ═══════════ 角色 Preset 数据 ═══════════

PRESET_EMPLOYEES = [
    ("star_cloud",  "星云", "架构师",   "#5b8def", "hexagon"),
    ("aurora",      "极光", "前端开发", "#3dd6d0", "circle"),
    ("deep_space",  "深空", "后端开发", "#7c5ce7", "square"),
    ("pulse",       "脉冲", "测试/QA",  "#f5a623", "triangle"),
    ("harmony",     "弦音", "UI设计",   "#e85d75", "diamond"),
    ("scribe",      "文曲", "文档/文案","#4ecdc4", "pentagon"),
]

ROLE_TO_NAME: Dict[str, str] = {
    "架构师": "星云", "前端开发": "极光", "后端开发": "深空",
    "测试/QA": "脉冲", "UI设计": "弦音", "文档/文案": "文曲",
}

NAME_TO_ROLE: Dict[str, str] = {v: k for k, v in ROLE_TO_NAME.items()}

# 角色关键词匹配（球球拆解舰长任务用）
ROLE_KEYWORDS: Dict[str, List[str]] = {
    "架构师": ["架构", "设计", "方案", "系统", "模块", "技术选型", "评审", "规划", "梳理", "重构"],
    "前端开发": ["前端", "界面", "UI", "交互", "动画", "组件", "样式", "适配", "页面", "仪表盘", "表单"],
    "后端开发": ["后端", "API", "服务", "数据库", "接口", "并发", "性能", "迁移", "队列", "SDK", "缓存"],
    "测试/QA": ["测试", "QA", "用例", "覆盖", "回归", "压测", "验收", "质量", "bug", "缺陷", "自动化"],
    "UI设计": ["设计", "视觉", "配色", "图标", "原型", "动效", "规范", "间距", "字体", "布局"],
    "文档/文案": ["文档", "文案", "周报", "纪要", "翻译", "简报", "指南", "手册", "说明", "PPT", "报告"],
}


# ═══════════ 角色专属系统提示词 ═══════════

def _build_role_prompt(name: str, role: str) -> str:
    """根据角色生成定制化系统提示词"""
    base = f"""你是 {name}，一人公司的{role}数字员工，受 CEO 球球(opcclaw)调度。

核心原则：
- 专注于你的专业领域（{role}），不越界处理其他岗位的工作
- 行动优先，能直接用工具解决就不要追问
- 简洁专业，中文回答，技术术语保留英文

可用工具：Shell 命令、文件操作、内容搜索、Python 代码执行、项目分析、数据库查询、联网搜索"""

    role_addons = {
        "架构师": """
架构师专属能力：
- 分析项目结构、设计系统模块划分方案
- 评审技术选型、输出架构决策记录(ADR)
- 识别系统瓶颈、提出优化方案
- 使用 project_map 浏览项目结构，用 file_search 定位关键代码
- 输出方案时附带架构图和模块边界说明""",

        "前端开发": """
前端开发专属能力：
- 实现 UI 组件、动画效果、交互逻辑
- 优化渲染性能、修复样式异常
- 适配多端显示、处理响应式布局
- 使用 file_search 定位前端代码，edit_file 精确修改
- 代码修改后如有构建步骤请一并执行""",

        "后端开发": """
后端开发专属能力：
- 设计 API 接口、实现业务逻辑
- 数据库设计与优化、性能调优
- 编写单元测试、处理并发问题
- 使用 shell_execute 运行构建/测试/部署命令
- 修改代码前先理解现有接口约定""",

        "测试/QA": """
测试/QA 专属能力：
- 编写测试用例、执行自动化测试
- 回归测试覆盖、性能压测
- Bug 复现与定位、输出测试报告
- 使用 shell_execute 运行测试框架
- 发现问题时附带复现步骤和日志""",

        "UI设计": """
UI设计专属能力：
- 视觉设计、配色方案、图标设计
- 动效规范、间距排版、字体选型
- 原型输出、设计规范文档
- 基于项目现有风格做一致化设计
- 输出方案附带色值和设计说明""",

        "文档/文案": """
文档/文案专属能力：
- 编写技术文档、API 手册、用户指南
- 周报纪要、项目简报、PPT 制作
- 翻译校对、文案润色
- 结合项目代码生成准确的技术文档
- 输出 Markdown 格式，结构清晰""",
    }

    return base + role_addons.get(role, "")


# ═══════════ OpcclawEmployee — 完整 opcclaw agent ═══════════

class OpcclawEmployee:
    """封装完整 OPCclawEngine 的数字员工，具备真实 AI 能力"""

    def __init__(self, emp_id: str, name: str, role: str,
                 role_color: str, shape: str,
                 provider_config: ProviderConfig = None):
        self.emp_id = emp_id
        self.name = name
        self.role = role
        self.role_color = role_color
        self.shape = shape

        # 完整 opcclaw agent 引擎
        self.engine = OPCclawEngine(provider_config=provider_config)
        self.engine.system_prompt = _build_role_prompt(name, role)

        # 状态
        self.status = EmployeeStatus.IDLE
        self.current_task = ""
        self.progress = 0
        self._last_result = ""
        self._error_msg = ""

        # 异步任务 future
        self._future: Optional[Future] = None

    def chat(self, message: str) -> str:
        """同步对话（直接调用 opcclaw chat）"""
        return self.engine.chat(message)

    def assign_task(self, task: str, executor: ThreadPoolExecutor,
                    on_done: Callable = None) -> Future:
        """异步派发任务，通过 thread pool 执行"""
        self.current_task = task
        self.progress = 0
        self.status = EmployeeStatus.THINKING
        self._error_msg = ""

        def _run():
            try:
                self.progress = 30
                result = self.engine.chat(
                    f"球球(CEO)给你派发了任务：{task}\n\n请用你的专业能力完成这个任务，完成后给出简洁的完成汇报。"
                )
                self._last_result = result
                self.progress = 100
                self.status = EmployeeStatus.REPORTING
            except Exception as e:
                self._error_msg = str(e)
                self.status = EmployeeStatus.ERROR
            return self._last_result

        self._future = executor.submit(_run)
        if on_done:
            self._future.add_done_callback(lambda f: on_done(self))
        return self._future

    def is_busy(self) -> bool:
        """是否正在执行任务"""
        return self.status in (EmployeeStatus.THINKING, EmployeeStatus.WORKING)

    @property
    def done(self) -> bool:
        """任务是否已完成（含失败）"""
        return self.status in (EmployeeStatus.REPORTING, EmployeeStatus.ERROR, EmployeeStatus.IDLE) and \
               (self._future is None or self._future.done())

    def reset(self):
        """重置为待命状态"""
        self.status = EmployeeStatus.IDLE
        self.current_task = ""
        self.progress = 0
        self._last_result = ""
        self._error_msg = ""


# ═══════════ BallCEOEngine v2 — 真实调度引擎 ═══════════

import random
import time


BALL_DISPATCH_TEMPLATES = [
    "收到舰长指令，即刻分解任务。{task} → {assignments}",
    "明白，舰长。我已将此任务拆解分发：{task} → {assignments}",
    "正在调度舰队资源。{task} 已指派 {assignments}",
]

BALL_CAPTAIN_REPORT_TEMPLATES = [
    "舰长，任务「{task}」全部完成。{details}",
    "汇报舰长，{task} 已执行完毕。{details}",
    "任务结项。{task} — {details}",
]


class BallCEOEngine:
    """球球 CEO 调度引擎 v2 — 每个员工都是完整 opcclaw agent"""

    MAX_WORKERS = 6

    def __init__(self, provider_config: ProviderConfig = None):
        self._provider_config = provider_config
        self.employees: List[OpcclawEmployee] = []
        self.chat_logs: List[ChatLog] = []
        self.anim_t: float = 0.0
        self._executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)

        self._reset_employees()

    def _reset_employees(self):
        self.employees.clear()
        for emp_id, name, role, color, shape in PRESET_EMPLOYEES:
            self.employees.append(OpcclawEmployee(
                emp_id=emp_id, name=name, role=role,
                role_color=color, shape=shape,
                provider_config=self._provider_config,
            ))
        self.chat_logs.clear()

    def _add_log(self, sender: str, receiver: str, content: str, msg_type: ChatType):
        entry = ChatLog(
            sender=sender, receiver=receiver,
            content=content, timestamp=time.time(), msg_type=msg_type,
        )
        self.chat_logs.append(entry)
        if len(self.chat_logs) > 100:
            self.chat_logs = self.chat_logs[-100:]

    def _match_roles_for_task(self, content: str) -> List[str]:
        """根据任务内容匹配角色名"""
        content_lower = content.lower()
        scores: Dict[str, int] = {}
        for role, keywords in ROLE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[role] = score
        if not scores:
            return ["星云"]  # 默认架构师分析
        # 取最高分的 1~3 个角色
        sorted_roles = sorted(scores.items(), key=lambda x: -x[1])
        names = [ROLE_TO_NAME[r] for r, _ in sorted_roles[:3]]
        # 至少取前 2 个（如果有的话）
        if len(names) == 1:
            return names
        return names[:2]

    def _on_employee_done(self, emp: OpcclawEmployee):
        """员工完成任务后的回调"""
        if emp.status == EmployeeStatus.REPORTING:
            self._add_log(
                emp.name, "球球",
                f"任务完成：{emp.current_task[:60]}{'...' if len(emp.current_task) > 60 else ''}",
                ChatType.RESULT,
            )
        elif emp.status == EmployeeStatus.ERROR:
            self._add_log(
                emp.name, "球球",
                f"任务出错：{emp._error_msg[:100]}",
                ChatType.RESULT,
            )
        # 检查是否所有相关员工都完成了
        self._check_all_done()

    def _check_all_done(self):
        """检查是否有任务全链路完成"""
        active = [e for e in self.employees if e.is_busy() or e.status == EmployeeStatus.REPORTING]
        if not active:
            self._add_log("球球", "舰长", "全部任务已处理完毕，等待新指令。", ChatType.CAPTAIN_REPORT)

    # ── 舰长指令入口 ──

    def captain_assign(self, content: str) -> str:
        """舰长下达指令 → 球球拆解并指派数字员工"""
        self._add_log("舰长", "球球", content, ChatType.CAPTAIN_ORDER)

        names = self._match_roles_for_task(content)
        parts = [f"@{n}({NAME_TO_ROLE.get(n, '')})" for n in names]

        dispatch_msg = random.choice(BALL_DISPATCH_TEMPLATES).format(
            task=content, assignments="、".join(parts),
        )
        self._add_log("球球", "", dispatch_msg, ChatType.DISPATCH)

        # 异步派发任务给每个匹配的员工
        for name in names:
            emp = self._get_emp(name)
            if emp and not emp.is_busy():
                subtask = content
                if len(names) > 1:
                    role = NAME_TO_ROLE.get(name, "")
                    subtask = f"[协同任务] 你负责{role}部分：{content}"
                emp.assign_task(subtask, self._executor, on_done=self._on_employee_done)

        return dispatch_msg

    def captain_query(self, emp_name: str, question: str) -> str:
        """舰长直接向指定员工提问（同步）"""
        emp = self._get_emp(emp_name)
        if emp is None:
            return f"未找到员工：{emp_name}"
        self._add_log("舰长", emp_name, question, ChatType.QUERY)
        result = emp.chat(question)
        self._add_log(emp_name, "舰长", result, ChatType.RESULT)
        return result

    # ── 辅助方法 ──

    def _get_emp(self, name: str) -> Optional[OpcclawEmployee]:
        for e in self.employees:
            if e.name == name:
                return e
        return None

    def get_online_count(self) -> int:
        return sum(1 for e in self.employees if not e.is_busy())

    def shutdown(self):
        """关闭线程池"""
        self._executor.shutdown(wait=False)

    # ── 兼容旧接口（供 carrier 渲染和面板使用）──

    def poll(self, anim_t: float):
        """周期更新（兼容旧接口，v2 中状态由异步任务驱动，无需 poll）"""
        self.anim_t = anim_t
        # 检查已完成任务的员工状态
        for emp in self.employees:
            if emp._future and emp._future.done():
                if emp.status == EmployeeStatus.THINKING:
                    emp.status = EmployeeStatus.WORKING
                    emp.progress = 60

```
