"""
多模型管理插件
支持多个 LLM 后端切换和对比
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    provider: str  # openai, anthropic, google, local
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    enabled: bool = True


class MultiModelPlugin:
    """多模型管理插件"""
    
    def __init__(self):
        self.config_file = os.path.expanduser("~/.opcclaw/models.json")
        self.models: Dict[str, ModelConfig] = {}
        self.active_model: str = ""
        self.load_configs()
    
    def load_configs(self):
        """加载模型配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for name, cfg in data.items():
                    self.models[name] = ModelConfig(**cfg)
            except Exception as e:
                print(f"[MultiModel] Load config failed: {e}")
    
    def save_configs(self):
        """保存模型配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(
                {k: asdict(v) for k, v in self.models.items()},
                f, ensure_ascii=False, indent=2
            )
    
    def add_model(self, config: ModelConfig) -> bool:
        """添加模型"""
        self.models[config.name] = config
        self.save_configs()
        return True
    
    def remove_model(self, name: str) -> bool:
        """删除模型"""
        if name in self.models:
            del self.models[name]
            if self.active_model == name:
                self.active_model = ""
            self.save_configs()
            return True
        return False
    
    def set_active(self, name: str) -> bool:
        """设置活跃模型"""
        if name in self.models and self.models[name].enabled:
            self.active_model = name
            return True
        return False
    
    def get_active(self) -> Optional[ModelConfig]:
        """获取活跃模型配置"""
        if self.active_model and self.active_model in self.models:
            return self.models[self.active_model]
        # 返回第一个启用的模型
        for name, cfg in self.models.items():
            if cfg.enabled:
                return cfg
        return None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有模型"""
        return [
            {
                "name": name,
                "provider": cfg.provider,
                "model": cfg.model,
                "enabled": cfg.enabled,
                "active": name == self.active_model
            }
            for name, cfg in self.models.items()
        ]
    
    def chat(self, message: str, model_name: str = None) -> Dict[str, Any]:
        """
        使用指定模型对话
        
        Args:
            message: 用户消息
            model_name: 模型名称（None 使用活跃模型）
        
        Returns:
            对话结果
        """
        cfg = self.models.get(model_name) if model_name else self.get_active()
        
        if not cfg:
            return {"success": False, "error": "没有可用的模型配置"}
        
        try:
            if cfg.provider == "openai" or cfg.provider == "openai_compatible":
                return self._chat_openai(cfg, message)
            elif cfg.provider == "anthropic":
                return self._chat_anthropic(cfg, message)
            elif cfg.provider == "google":
                return self._chat_google(cfg, message)
            else:
                return {"success": False, "error": f"不支持的提供商: {cfg.provider}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat_openai(self, cfg: ModelConfig, message: str) -> Dict[str, Any]:
        """使用 OpenAI 格式 API"""
        import urllib.request
        
        payload = json.dumps({
            "model": cfg.model,
            "messages": [{"role": "user", "content": message}],
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens
        }).encode()
        
        req = urllib.request.Request(
            f"{cfg.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {cfg.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode())
        
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            return {
                "success": True,
                "response": content,
                "model": cfg.name,
                "usage": data.get("usage", {})
            }
        
        return {"success": False, "error": "Empty response"}
    
    def _chat_anthropic(self, cfg: ModelConfig, message: str) -> Dict[str, Any]:
        """使用 Anthropic API"""
        import urllib.request
        
        payload = json.dumps({
            "model": cfg.model,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": cfg.max_tokens
        }).encode()
        
        req = urllib.request.Request(
            f"{cfg.base_url}/messages",
            data=payload,
            headers={
                "x-api-key": cfg.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode())
        
        content = data.get("content", [])
        if content:
            return {
                "success": True,
                "response": content[0].get("text", ""),
                "model": cfg.name,
                "usage": data.get("usage", {})
            }
        
        return {"success": False, "error": "Empty response"}
    
    def _chat_google(self, cfg: ModelConfig, message: str) -> Dict[str, Any]:
        """使用 Google Gemini API"""
        import urllib.request
        
        payload = json.dumps({
            "contents": [{"parts": [{"text": message}]}],
            "generationConfig": {
                "temperature": cfg.temperature,
                "maxOutputTokens": cfg.max_tokens
            }
        }).encode()
        
        req = urllib.request.Request(
            f"{cfg.base_url}/models/{cfg.model}:generateContent?key={cfg.api_key}",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode())
        
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {
                "success": True,
                "response": content,
                "model": cfg.name
            }
        
        return {"success": False, "error": "Empty response"}
    
    def compare_models(self, message: str, model_names: List[str]) -> Dict[str, Any]:
        """对比多个模型的回答"""
        results = {}
        for name in model_names:
            if name in self.models:
                results[name] = self.chat(message, name)
        return {"success": True, "comparisons": results}


def initialize(plugin_manager):
    """插件初始化"""
    plugin = MultiModelPlugin()
    plugin_manager.multi_model = plugin
    print("[MultiModel] Plugin loaded")
