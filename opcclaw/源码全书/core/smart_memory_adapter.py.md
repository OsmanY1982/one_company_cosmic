# `core/smart_memory_adapter.py`

> 路径：`core/smart_memory_adapter.py` | 行数：192


---


```python
"""
Smart Memory Adapter
桥接旧版 MemoryStore 与新版 SmartMemory
保持向后兼容的同时提供增强功能
"""

import os
from typing import Optional, Dict, List
from .memory_store import MemoryStore
from .smart_memory import SmartMemory


class SmartMemoryStore:
    """
    增强版记忆存储
    
    同时兼容旧版 MemoryStore API 和新增 SmartMemory 功能
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        # 初始化旧版存储（会话持久化）
        self._legacy = MemoryStore(base_dir)
        
        # 初始化新版智能记忆
        project_root = base_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "opcclaw"
        )
        self._smart = SmartMemory(project_root)
    
    # ================================
    # 旧版 API（完全兼容）
    # ================================
    
    def save_session(self, messages: list[dict], session_id: str = "default") -> str:
        """保存会话（旧版）"""
        return self._legacy.save_session(messages, session_id)
    
    def load_session(self, session_id: str = "default") -> list[dict]:
        """加载会话（旧版）"""
        return self._legacy.load_session(session_id)
    
    def list_sessions(self) -> list[dict]:
        """列���会话（旧版）"""
        return self._legacy.list_sessions()
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话（旧版）"""
        return self._legacy.delete_session(session_id)
    
    def read_memory(self, name: str) -> str:
        """读取记忆（旧版）"""
        return self._legacy.read_memory(name)
    
    def write_memory(self, name: str, content: str) -> str:
        """写入记忆（旧版）"""
        return self._legacy.write_memory(name, content)
    
    def append_memory(self, name: str, content: str) -> str:
        """追加记忆（旧版）"""
        return self._legacy.append_memory(name, content)
    
    def list_memories(self) -> list[str]:
        """列出记忆（旧版）"""
        return self._legacy.list_memories()
    
    def save_fact(self, fact: str):
        """保存事实（旧版）"""
        # 同时写入智能记忆的检索画像
        self._smart.update_retrieval_profile({
            "stable_domains": [fact[:50]]  # 提取关键信息
        })
        return self._legacy.save_fact(fact)
    
    def get_facts(self) -> str:
        """获取事实（旧版）"""
        return self._legacy.get_facts()
    
    def save_task(self, task: str):
        """保存任务（旧版）"""
        return self._legacy.save_task(task)
    
    def get_tasks(self) -> str:
        """获取任务（旧版）"""
        return self._legacy.get_tasks()
    
    # ================================
    # 新增智能记忆 API
    # ================================
    
    @property
    def smart(self) -> SmartMemory:
        """访问底层 SmartMemory 实例"""
        return self._smart
    
    def learn_from_interaction(self, user_message: str, assistant_response: str, 
                               feedback: Optional[str] = None) -> Dict:
        """
        从交互中学习
        
        Args:
            user_message: 用户消息
            assistant_response: 助手回复
            feedback: 用户反馈（"positive"/"negative"/None）
        """
        # 更新学习特征（简化实现）
        self._smart.update_learned_features({
            "vocabulary": {
                "high_freq_words": self._extract_keywords(user_message),
                "updated_at": __import__('datetime').datetime.now().isoformat()
            }
        })
        
        # 记录反馈
        if feedback == "positive":
            self._smart.record_accepted_suggestion(
                assistant_response[:100], 
                "用户正面反馈"
            )
        elif feedback == "negative":
            self._smart.record_rejected_suggestion(
                assistant_response[:100],
                "用户负面反馈"
            )
        
        return {"success": True, "learned": True}
    
    def _extract_keywords(self, text: str) -> Dict[str, int]:
        """提取关键词（简化实现）"""
        # 实际应用中可以使用更复杂的NLP
        if text is None:
            text = ''
        words = text.lower().split()
        freq = {}
        for word in words:
            if len(word) > 2:
                freq[word] = freq.get(word, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def get_personalized_context(self) -> str:
        """获取个性化上下文（用于注入到LLM提示中）"""
        profile = self._smart.get_user_profile()
        preferences = self._smart._load_preference_profile()
        
        context_parts = []
        
        # 用户偏好
        if preferences.get("writing_style"):
            style = preferences["writing_style"]
            context_parts.append(f"用户偏好语气: {style.get('tone', 'professional')}")
            context_parts.append(f"正式程度: {style.get('formality', 'medium')}")
        
        # 学习状态
        if preferences.get("learning_state", {}).get("is_frozen"):
            context_parts.append("[注意：学习系统当前已冻结]")
        
        # 检索画像
        retrieval = self._smart.get_retrieval_profile()
        if retrieval.get("stable_domains"):
            context_parts.append(f"稳定领域: {', '.join(retrieval['stable_domains'][:5])}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def should_adapt_content(self, content_type: str = "general") -> bool:
        """检查是否应该对内容进行个性化适配"""
        # 检查保护内容类型
        if content_type in SmartMemory.BOUNDARIES["protected_content_types"]:
            return False
        
        # 检查是否冻结
        profile = self._smart._load_preference_profile()
        if profile.get("learning_state", {}).get("is_frozen"):
            return False
        
        # 检查是否启用
        return self._smart.options["enabled"]
    
    def get_stats(self) -> Dict:
        """获取完整统计信息"""
        return {
            "legacy": {
                "sessions": len(self._legacy.list_sessions()),
                "memories": len(self._legacy.list_memories())
            },
            "smart": self._smart.get_stats()
        }


# 便捷函数
def create_memory_store(base_dir: Optional[str] = None) -> SmartMemoryStore:
    """创建增强版记忆存储实例"""
    return SmartMemoryStore(base_dir)

```
