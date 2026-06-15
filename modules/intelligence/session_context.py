"""全局会话上下文 — 统一悬浮球/智能中心/语音的AI对话状态"""
from datetime import datetime
from typing import Optional, Callable, List
import threading


class SessionContext:
    """
    全局单例：维护当前活跃的AI对话会话。
    悬浮球、智能中心、语音三个入口共享同一会话，切换即全局生效。
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._current_session_id: str = "default"
        self._current_title: str = "对话"
        self._agent_bridge = None            # AgentBridge 引用
        self._active_window = None           # 当前活跃的 AIChatWindow
        self._listeners: List[Callable] = [] # 会话切换监听器
        
    def set_agent_bridge(self, bridge):
        """设置引擎引用（由悬浮球或智能中心初始化时注入）"""
        self._agent_bridge = bridge
        
    @property
    def agent_bridge(self):
        return self._agent_bridge
    
    @property
    def current_session_id(self) -> str:
        return self._current_session_id
    
    @property
    def current_title(self) -> str:
        return self._current_title
    
    def switch_session(self, session_id: str, title: str = "对话"):
        """切换当前活跃会话（全局生效）"""
        self._current_session_id = session_id
        self._current_title = title
        self._notify_listeners(session_id, title)
    
    def new_session(self) -> str:
        """创建新会话并设为当前"""
        sid = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.switch_session(sid, "新对话")
        return sid
    
    def register_window(self, window):
        """注册活跃的对话窗口"""
        self._active_window = window
        
    def unregister_window(self, window):
        """注销对话窗口"""
        if self._active_window is window:
            self._active_window = None
    
    def add_listener(self, callback: Callable):
        """添加会话切换监听器"""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """移除监听器"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, session_id: str, title: str):
        """通知所有监听器会话已切换"""
        for cb in self._listeners:
            try:
                cb(session_id, title)
            except Exception as e:
                print(f"[SessionContext] 监听器异常: {e}")


# 全局单例实例
session_ctx = SessionContext()
