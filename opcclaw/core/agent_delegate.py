"""
OPCclaw Agent Delegate - 子代理委托系统

提供:
- 简化的子代理派生
- 隔离上下文执行
- 结果汇总
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SubAgentTask:
    """子代理任务"""
    goal: str
    context: str = ""
    toolsets: List[str] = None
    result: Optional[Dict] = None
    status: str = "pending"  # pending, running, completed, failed


class AgentDelegate:
    """子代理委托管理器"""
    
    def __init__(self, python_path: str = None):
        self.python_path = python_path or sys.executable
        self.tasks: Dict[str, SubAgentTask] = {}
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, name: str, func: Callable):
        """注册任务处理器"""
        self.handlers[name] = func
    
    def delegate_task(self, task_id: str, goal: str, context: str = "", 
                     toolsets: List[str] = None) -> SubAgentTask:
        """
        委托任务给子代理
        
        Args:
            task_id: 任务 ID
            goal: 任务目标
            context: 背景信息
            toolsets: 启用的工具集
            
        Returns:
            SubAgentTask
        """
        task = SubAgentTask(
            goal=goal,
            context=context,
            toolsets=toolsets or [],
            status="pending"
        )
        
        self.tasks[task_id] = task
        return task
    
    def execute_task(self, task_id: str) -> Dict:
        """
        执行任务（同步模式）
        
        实际生产环境可以派生独立进程，这里使用简化实现
        """
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"任务不存在: {task_id}"}
        
        task.status = "running"
        
        try:
            # 查找匹配的处理器
            handler = self._find_handler(task.goal)
            if handler:
                result = handler(task.context, task.toolsets)
                task.result = result
                task.status = "completed"
            else:
                # 默认执行：记录任务信息
                task.result = {
                    "goal": task.goal,
                    "context": task.context,
                    "executed_at": time.time()
                }
                task.status = "completed"
            
            return {"success": True, "result": task.result}
            
        except Exception as e:
            task.result = {"error": str(e)}
            task.status = "failed"
            return {"success": False, "error": str(e)}
    
    def _find_handler(self, goal: str) -> Optional[Callable]:
        """根据目标查找匹配的处理器"""
        goal_lower = goal.lower()
        
        # 关键词匹配
        for handler_name, handler_func in self.handlers.items():
            if handler_name.lower() in goal_lower:
                return handler_func
        
        return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if task:
            return {
                "task_id": task_id,
                "goal": task.goal,
                "status": task.status,
                "result": task.result
            }
        return None
    
    def list_tasks(self) -> List[Dict]:
        """列出所有任务"""
        return [
            {
                "task_id": tid,
                "goal": t.goal,
                "status": t.status,
                "result": t.result
            }
            for tid, t in self.tasks.items()
        ]
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status == "pending":
            task.status = "cancelled"
            return True
        return False


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_delegate = None

def get_agent_delegate(python_path: str = None) -> AgentDelegate:
    global _delegate
    if _delegate is None:
        _delegate = AgentDelegate(python_path)
    return _delegate
