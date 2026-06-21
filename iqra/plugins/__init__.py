"""
Iqra 插件系统
支持动态加载扩展功能
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import importlib
import os
import sys


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    enabled: bool = True
    entry_point: str = ""  # 模块路径


class PluginManager:
    """
    插件管理器
    - 动态加载/卸载插件
    - 插件间通信
    - 生命周期管理
    """
    
    def __init__(self, plugin_dirs: List[str] = None):
        self.plugins: Dict[str, Any] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.plugin_dirs = plugin_dirs or []
        
    def discover_plugins(self) -> List[PluginInfo]:
        """发现可用插件"""
        discovered = []
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
            for item in os.listdir(plugin_dir):
                plugin_path = os.path.join(plugin_dir, item)
                if os.path.isdir(plugin_path):
                    # 检查是否有 __init__.py 或 plugin.json
                    init_file = os.path.join(plugin_path, "__init__.py")
                    config_file = os.path.join(plugin_path, "plugin.json")
                    
                    if os.path.exists(config_file):
                        import json
                        with open(config_file, "r", encoding="utf-8") as f:
                            config = json.load(f)
                        info = PluginInfo(
                            name=config.get("name", item),
                            version=config.get("version", "0.1.0"),
                            description=config.get("description", ""),
                            author=config.get("author", ""),
                            entry_point=config.get("entry_point", item)
                        )
                        discovered.append(info)
                    elif os.path.exists(init_file):
                        discovered.append(PluginInfo(
                            name=item,
                            version="0.1.0",
                            description="",
                            author="",
                            entry_point=item
                        ))
        return discovered
    
    def load_plugin(self, info: PluginInfo) -> bool:
        """加载插件"""
        try:
            # 添加到路径
            for plugin_dir in self.plugin_dirs:
                if plugin_dir not in sys.path:
                    sys.path.insert(0, plugin_dir)
            
            # 导入模块
            module = importlib.import_module(info.entry_point)
            
            # 初始化插件
            if hasattr(module, "initialize"):
                module.initialize(self)
            
            self.plugins[info.name] = module
            self.plugin_info[info.name] = info
            return True
        except Exception as e:
            print(f"[PluginManager] Failed to load {info.name}: {e}")
            return False
    
    def unload_plugin(self, name: str):
        """卸载插件"""
        if name in self.plugins:
            plugin = self.plugins[name]
            if hasattr(plugin, "shutdown"):
                plugin.shutdown()
            del self.plugins[name]
            del self.plugin_info[name]
    
    def register_hook(self, event: str, callback: Callable):
        """注册事件钩子"""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(callback)
    
    def trigger_hook(self, event: str, *args, **kwargs) -> List[Any]:
        """触发事件钩子"""
        results = []
        for callback in self.hooks.get(event, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"[PluginManager] Hook error in {event}: {e}")
        return results
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """获取已加载的插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[PluginInfo]:
        """列出所有插件信息"""
        return list(self.plugin_info.values())
