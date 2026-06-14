
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字员工数据模型 + 模拟引擎
舰队指挥系统 · 数字员工层
舰长 → 球球(CEO) → 数字员工 三级指挥链
"""
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


# ── 员工状态枚举 ─────────────────────────────────
class EmployeeStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    REPORTING = "reporting"


# ── 消息类型枚举 ─────────────────────────────────
class ChatType(Enum):
    ASSIGN = "assign"                # 球球派活
    REPORT = "report"                # 员工汇报
    QUERY = "query"                  # 员工请示
    CAPTAIN_ORDER = "captain_order"  # 舰长下令
    DISPATCH = "dispatch"            # 球球拆解调度
    CAPTAIN_REPORT = "captain_report"  # 球球向舰长汇报


# ── 舰长任务状态 ────────────────────────────────
class CaptainTaskStatus(Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    DONE = "done"


# ── 数据类 ───────────────────────────────────────

@dataclass
class ChatLog:
    sender: str          # "舰长" / "球球" / 员工名
    receiver: str        # "舰长" / "球球" / 员工名 / ""(广播)
    content: str
    timestamp: float
    msg_type: ChatType


@dataclass
class CaptainTask:
    task_id: int
    content: str
    status: CaptainTaskStatus = CaptainTaskStatus.PENDING
    created_at: float = 0.0
    assigned_to: List[str] = field(default_factory=list)
    dispatch_time: float = 0.0


@dataclass
class DigitalEmployee:
    emp_id: str
    name: str
    role: str
    role_color: str
    shape: str
    status: EmployeeStatus = EmployeeStatus.IDLE
    current_task: str = ""
    progress: int = 0
    mood: str = "😐"
    think_start: float = 0.0
    work_start: float = 0.0
    think_duration: float = 0.0
    work_duration: float = 0.0
    report_start: float = 0.0
    captain_task_id: int = -1

    def reset(self):
        self.status = EmployeeStatus.IDLE
        self.current_task = ""
        self.progress = 0
        self.mood = "😐"
        self.captain_task_id = -1


# ── 角色关键词匹配（球球拆解舰长任务用） ──────────
ROLE_KEYWORDS: Dict[str, List[str]] = {
    "架构师": ["架构", "设计", "方案", "系统", "模块", "技术选型", "评审", "规划", "梳理", "重构"],
    "前端开发": ["前端", "界面", "UI", "交互", "动画", "组件", "样式", "适配", "页面", "仪表盘", "表单"],
    "后端开发": ["后端", "API", "服务", "数据库", "接口", "并发", "性能", "迁移", "队列", "SDK", "缓存", "消息"],
    "测试/QA": ["测试", "QA", "用例", "覆盖", "回归", "压测", "验收", "质量", "bug", "缺陷", "自动化"],
    "UI设计": ["设计", "视觉", "配色", "图标", "原型", "动效", "规范", "样式", "间距", "字体", "布局"],
    "文档/文案": ["文档", "文案", "周报", "纪要", "翻译", "简报", "指南", "手册", "说明", "PPT", "报告"],
}


# ── 预设任务池（按角色匹配） ──────────────────────

ROLE_TASK_POOL: Dict[str, List[str]] = {
    "架构师": [
        "设计系统模块划分方案",
        "评审技术方案可行性",
        "绘制核心架构图",
        "制定技术选型标准",
        "分析系统瓶颈并输出优化方案",
        "编写架构决策记录(ADR)",
        "梳理微服务边界",
    ],
    "前端开发": [
        "实现指挥台仪表盘组件",
        "优化动画帧率至60fps",
        "修复深色主题样式异常",
        "开发可复用卡片组件",
        "适配悬浮球交互手势",
        "编写前端单元测试",
        "重构状态管理层代码",
    ],
    "后端开发": [
        "设计API接口规范",
        "优化数据库查询性能",
        "实现消息队列消费者",
        "编写数据迁移脚本",
        "处理并发请求限流逻辑",
        "集成第三方服务SDK",
        "修复内存泄漏问题",
    ],
    "测试/QA": [
        "编写自动化回归测试用例",
        "执行压力测试并输出报告",
        "验证最新版本修复项",
        "搭建持续集成流水线",
        "分析线上异常日志",
        "制定边界条件测试方案",
        "评审需求文档测试点",
    ],
    "UI设计": [
        "设计暗色主题配色方案",
        "绘制交互流程图",
        "输出组件规范文档",
        "优化卡片圆角和阴影",
        "设计状态指示灯动效",
        "制作高保真原型",
        "调整字体层级和间距",
    ],
    "文档/文案": [
        "编写API接口文档",
        "更新版本发布说明",
        "整理技术分享PPT",
        "撰写项目周报",
        "翻译技术文档英文版",
        "编写新人入职指南",
        "整理会议纪要",
    ],
}

BALL_MESSAGES = [
    "收到，我来安排。",
    "这个方向很好，继续推进。",
    "有风险及时同步，别闷头干。",
    "注意时间节点，优先保证核心功能。",
    "辛苦了，汇报得很清晰。",
    "架构上再斟酌一下，别过度设计。",
    "测试覆盖率要达到85%以上。",
    "文档可以再精简一些，突出关键决策。",
    "和前端对齐一下接口格式。",
    "暂时没有新任务，待命。",
]

BALL_CAPTAIN_REPORT_TEMPLATES = [
    "舰长，任务「{task}」已完成。{details}",
    "向舰长汇报：{task} 已全部落实。{details}",
    "舰长，您交代的「{task}」已完成，{details}",
]

BALL_DISPATCH_TEMPLATES = [
    "舰长有新任务：{task}，{assignments}，大家各就各位。",
    "收到舰长指令「{task}」，{assignments}，立即执行。",
    "@全员 舰长下达任务：{task}。{assignments}",
]


PRESET_EMPLOYEES: List[DigitalEmployee] = [
    DigitalEmployee("star_cloud",   "星云", "架构师",   "#5b8def", "hexagon"),
    DigitalEmployee("aurora",       "极光", "前端开发", "#3dd6d0", "circle"),
    DigitalEmployee("deep_space",   "深空", "后端开发", "#7c5ce7", "square"),
    DigitalEmployee("pulse",        "脉冲", "测试/QA",  "#f5a623", "triangle"),
    DigitalEmployee("harmony",      "弦音", "UI设计",   "#e85d75", "diamond"),
    DigitalEmployee("scribe",       "文曲", "文档/文案","#4ecdc4", "pentagon"),
]

ROLE_TO_NAME: Dict[str, str] = {
    "架构师": "星云",
    "前端开发": "极光",
    "后端开发": "深空",
    "测试/QA": "脉冲",
    "UI设计": "弦音",
    "文档/文案": "文曲",
}

NAME_TO_ROLE: Dict[str, str] = {v: k for k, v in ROLE_TO_NAME.items()}


# ── 球球调度引擎 ─────────────────────────────────

class BallCEOEngine:
    """球球 CEO 调度引擎"""

    MAX_CAPTAIN_TASKS = 3

    def __init__(self):
        self.employees: List[DigitalEmployee] = []
        self.chat_logs: List[ChatLog] = []
        self._captain_tasks: List[CaptainTask] = []
        self._captain_task_id_counter: int = 0
        self.anim_t: float = 0.0
        self._next_dispatch_time: float = 0.0
        self._pending_acks: List[dict] = []
        self._pending_dispatches: List[dict] = []
        self._pending_assignments: List[dict] = []
        self._reset_employees()

    def _reset_employees(self):
        self.employees = []
        for e in PRESET_EMPLOYEES:
            self.employees.append(DigitalEmployee(
                emp_id=e.emp_id, name=e.name, role=e.role,
                role_color=e.role_color, shape=e.shape,
            ))
        self.chat_logs.clear()
        self._captain_tasks.clear()
        self._captain_task_id_counter = 0
        self._next_dispatch_time = 0.0
        self._pending_acks.clear()
        self._pending_dispatches.clear()
        self._pending_assignments.clear()

    def _random_dispatch_interval(self) -> float:
        return random.uniform(8.0, 15.0)

    def _pick_task(self, role: str) -> str:
        pool = ROLE_TASK_POOL.get(role, ["处理日常事务"])
        return random.choice(pool)

    def _add_log(self, sender: str, receiver: str, content: str, msg_type: ChatType):
        entry = ChatLog(
            sender=sender, receiver=receiver,
            content=content, timestamp=self.anim_t, msg_type=msg_type,
        )
        self.chat_logs.append(entry)
        if len(self.chat_logs) > 50:
            self.chat_logs = self.chat_logs[-50:]

    # ── 舰长指令入口 ─────────────────────────────

    def captain_assign(self, content: str) -> bool:
        if len([t for t in self._captain_tasks if t.status != CaptainTaskStatus.DONE]) >= self.MAX_CAPTAIN_TASKS:
            return False

        self._captain_task_id_counter += 1
        tid = self._captain_task_id_counter
        task = CaptainTask(task_id=tid, content=content, created_at=self.anim_t)
        self._captain_tasks.append(task)

        self._add_log("舰长", "球球", content, ChatType.CAPTAIN_ORDER)
        self._pending_acks.append({"task_id": tid, "ack_time": self.anim_t + 2.0})
        self._pending_dispatches.append({
            "task_id": tid,
            "dispatch_time": self.anim_t + random.uniform(3.0, 5.0),
        })
        return True

    def _match_roles_for_task(self, content: str) -> List[str]:
        matched: Dict[str, int] = {}
        for role, keywords in ROLE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                matched[role] = score
        if not matched:
            all_roles = list(ROLE_TO_NAME.keys())
            count = random.randint(2, 3)
            matched = {r: 1 for r in random.sample(all_roles, count)}
        sorted_roles = sorted(matched.items(), key=lambda x: -x[1])
        selected = sorted_roles[:min(3, len(sorted_roles))]
        return [ROLE_TO_NAME[role] for role, _ in selected]

    def _make_subtask(self, content: str, role: str) -> str:
        subtasks = {
            "架构师": f"设计「{content}」的系统架构",
            "前端开发": f"实现「{content}」的前端界面",
            "后端开发": f"开发「{content}」的后端服务",
            "测试/QA": f"编写「{content}」的测试用例并验证",
            "UI设计": f"设计「{content}」的视觉方案",
            "文档/文案": f"撰写「{content}」的相关文档",
        }
        return subtasks.get(role, f"执行「{content}」相关任务")

    def _get_emp(self, name: str) -> Optional[DigitalEmployee]:
        for e in self.employees:
            if e.name == name:
                return e
        return None

    def _find_captain_task(self, tid: int) -> Optional[CaptainTask]:
        for t in self._captain_tasks:
            if t.task_id == tid:
                return t
        return None

    # ── 主循环 ───────────────────────────────────

    def poll(self, anim_t: float):
        self.anim_t = anim_t

        # ① 球球确认舰长指令
        remaining = []
        for ack in self._pending_acks:
            if anim_t >= ack["ack_time"]:
                task = self._find_captain_task(ack["task_id"])
                if task:
                    self._add_log("球球", "舰长", "收到，舰长。我这就安排。", ChatType.CAPTAIN_REPORT)
            else:
                remaining.append(ack)
        self._pending_acks = remaining

        # ② 球球拆解任务
        remaining = []
        for disp in self._pending_dispatches:
            if anim_t >= disp["dispatch_time"]:
                task = self._find_captain_task(disp["task_id"])
                if task and task.status == CaptainTaskStatus.PENDING:
                    names = self._match_roles_for_task(task.content)
                    task.assigned_to = names
                    task.dispatch_time = anim_t

                    parts = [f"@{n}({NAME_TO_ROLE.get(n, '')})" for n in names]
                    msg = random.choice(BALL_DISPATCH_TEMPLATES).format(
                        task=task.content, assignments="、".join(parts),
                    )
                    self._add_log("球球", "", msg, ChatType.DISPATCH)
                    task.status = CaptainTaskStatus.DISPATCHED

                    self._pending_assignments.append({
                        "task_id": task.task_id,
                        "names": names,
                        "assign_time": anim_t + random.uniform(1.0, 2.0),
                    })
            else:
                remaining.append(disp)
        self._pending_dispatches = remaining

        # ③ 球球指派员工
        remaining = []
        for asgn in self._pending_assignments:
            if anim_t >= asgn["assign_time"]:
                task = self._find_captain_task(asgn["task_id"])
                for name in asgn["names"]:
                    emp = self._get_emp(name)
                    if emp and emp.status == EmployeeStatus.IDLE:
                        role = NAME_TO_ROLE.get(name, "")
                        subtask = self._make_subtask(task.content, role) if task else ""
                        emp.current_task = subtask
                        emp.status = EmployeeStatus.THINKING
                        emp.mood = "🤔"
                        emp.progress = 0
                        emp.think_start = anim_t
                        emp.think_duration = random.uniform(2.0, 5.0)
                        emp.captain_task_id = asgn["task_id"]
                        self._add_log("球球", name, f"舰长任务指派：{subtask}", ChatType.ASSIGN)
            else:
                remaining.append(asgn)
        self._pending_assignments = remaining

        # ④ 检查舰长任务完成
        for task in self._captain_tasks:
            if task.status != CaptainTaskStatus.DISPATCHED:
                continue
            all_done = True
            details = []
            for name in task.assigned_to:
                emp = self._get_emp(name)
                if emp is None:
                    continue
                if emp.captain_task_id == task.task_id:
                    all_done = False
                else:
                    details.append(f"{name}已完成")
            if all_done and details:
                report = random.choice(BALL_CAPTAIN_REPORT_TEMPLATES).format(
                    task=task.content, details="，".join(details),
                )
                self._add_log("球球", "舰长", report, ChatType.CAPTAIN_REPORT)
                task.status = CaptainTaskStatus.DONE

        # ═══════ 员工状态机 ═══════
        for emp in self.employees:
            if emp.status == EmployeeStatus.THINKING:
                if anim_t - emp.think_start >= emp.think_duration:
                    emp.status = EmployeeStatus.WORKING
                    emp.mood = "🧑‍💻"
                    emp.progress = 0
                    emp.work_start = anim_t
                    emp.work_duration = random.uniform(3.0, 8.0)
                    self._add_log(emp.name, "球球",
                                  f"方案已确定，开始执行「{emp.current_task}」。", ChatType.QUERY)

            elif emp.status == EmployeeStatus.WORKING:
                elapsed = anim_t - emp.work_start
                if emp.work_duration > 0:
                    emp.progress = min(100, int(elapsed / emp.work_duration * 100))
                    if emp.progress < 30: emp.mood = "🔧"
                    elif emp.progress < 70: emp.mood = "⚙️"
                    elif emp.progress < 100: emp.mood = "✅"
                if elapsed >= emp.work_duration:
                    emp.status = EmployeeStatus.REPORTING
                    emp.progress = 100
                    emp.mood = "📋"
                    emp.report_start = anim_t
                    self._add_log(emp.name, "球球",
                                  f"「{emp.current_task}」已完成，请审核。", ChatType.REPORT)

            elif emp.status == EmployeeStatus.REPORTING:
                if anim_t - emp.report_start >= random.uniform(2.0, 4.0):
                    self._add_log("球球", emp.name, random.choice(BALL_MESSAGES), ChatType.ASSIGN)
                    emp.status = EmployeeStatus.IDLE
                    emp.current_task = ""
                    emp.progress = 0
                    emp.mood = "😐"
                    emp.think_start = 0.0
                    emp.work_start = 0.0
                    emp.report_start = 0.0
                    emp.captain_task_id = -1

        # ═══════ 球球普通派活 ═══════
        if anim_t >= self._next_dispatch_time:
            idle = [e for e in self.employees if e.status == EmployeeStatus.IDLE]
            if idle:
                target = random.choice(idle)
                task = self._pick_task(target.role)
                target.current_task = task
                target.status = EmployeeStatus.THINKING
                target.mood = "🤔"
                target.progress = 0
                target.think_start = anim_t
                target.think_duration = random.uniform(2.0, 5.0)
                target.captain_task_id = -1
                self._add_log("球球", target.name,
                              f"新任务指派：{task}，先想一下方案。", ChatType.ASSIGN)
            self._next_dispatch_time = anim_t + self._random_dispatch_interval()

    def get_online_count(self) -> int:
        return sum(1 for e in self.employees if e.status != EmployeeStatus.IDLE)

    def get_recent_logs(self, n: int = 50) -> List[ChatLog]:
        return self.chat_logs[-n:]

    @property
    def pending_captain_count(self) -> int:
        return len([t for t in self._captain_tasks if t.status != CaptainTaskStatus.DONE])
