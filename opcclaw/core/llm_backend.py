"""
OPCclaw LLM Backend - 多供应商统一接口
Universal multi-provider LLM interface with function calling.

内置模板: DeepSeek(V3/R1) | OpenAI | 通义千问 | 智谱GLM | Moonshot |
          百度千帆 | 讯飞星火 | Groq | Together AI | OpenRouter | SiliconFlow |
          Mistral | Perplexity | Fireworks | Cohere | MiniMax | 阶跃星辰 |
          Ollama | LM Studio | vLLM | llama.cpp | 自定义

特性:
- 统一 chat() / chat_stream() 接口
- 原生 Function Calling 支持
- 自动供应商检测
- 本地模型 SSL 自签证书兼容
- 纯标准库实现, 零额外依赖
"""

import json
import urllib.request
import urllib.error
import ssl
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator, Optional, Any


# Token 优化系统
try:
    from opcclaw.core.token_optimizer import TokenSaverMode, optimize_messages
except ImportError:
    # 如果导入失败，创建简单的替代函数
    class TokenSaverMode:
        def __init__(self, mode="balanced"):
            self.mode = mode
        
        def optimize(self, messages):
            return messages
    
    def optimize_messages(messages, mode="balanced"):
        return messages

@dataclass
class ProviderConfig:
    """LLM 供应商配置"""
    name: str                        # 显示名称
    provider_type: str               # "openai_compatible" | "anthropic" | "google"
    base_url: str = ""               # API 端点
    api_key: str = ""                # API Key (本地模型可为空)
    model: str = ""                  # 默认模型名
    temperature: float = 0.7
    max_tokens: int = 262144
    extra_headers: dict = field(default_factory=dict)
    description: str = ""            # 描述文字
    available_models: list = field(default_factory=list)  # 已知模型列表 (UI 下拉预填)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "extra_headers": self.extra_headers,
            "description": self.description,
            "available_models": self.available_models,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProviderConfig":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid_keys})


@dataclass
class ToolDefinition:
    """工具函数定义"""
    name: str                        # 函数名
    description: str                 # 功能描述
    parameters: dict                 # JSON Schema 参数定义
    handler: Optional[callable] = None  # 实际执行的 Python 函数
    category: str = ""               # 工具分类（可选）

    def to_openai_schema(self) -> dict:
        """转为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class ToolCall:
    """LLM 请求的工具调用"""
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: Optional[str] = None          # 文本内容
    reasoning: Optional[str] = None        # 推理内容（qwen3.6 等 reasoning 模型）
    tool_calls: Optional[list[ToolCall]] = None  # 工具调用列表
    finish_reason: str = "stop"
    model: str = ""
    usage: dict = field(default_factory=dict)
    is_tool_call: bool = False             # 是否为工具调用响应


# ═══════════════════════════════════════════
# 抽象基类
# ═══════════════════════════════════════════

class BaseLLMBackend(ABC):
    """所有 LLM 后端的抽象基类"""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """
        发送消息并获取响应。

        Args:
            messages: [{"role": "user", "content": "..."}, ...]
            tools: OpenAI 格式的工具定义列表
            tool_choice: "auto" | "required" | "none" - 是否强制使用工具

        Returns:
            LLMResponse (可能包含文本或 tool_calls)
        """
        ...

    def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> Iterator[LLMResponse]:
        """
        流式版本。默认降级为非流式。
        子类可覆盖实现真正的 SSE 流式。
        """
        yield self.chat(messages, tools, tool_choice=tool_choice)

    def supports_tools(self) -> bool:
        """是否支持原生 function calling"""
        return False


# ═══════════════════════════════════════════
# OpenAI 兼容后端 (覆盖 95% 场景)
# ═══════════════════════════════════════════

class OpenAICompatibleBackend(BaseLLMBackend):
    """
    通用 OpenAI 兼容后端。

    支持: OpenAI, DeepSeek, Ollama, vLLM, LM Studio,
          通义千问, 智谱GLM, Moonshot, 百度文心, 讯飞星火,
          Groq, Together AI, OpenRouter, SiliconFlow, 任意自定义端点
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # SSL: 本地模型自签证书 / 阿里云百炼 hostname mismatch
        _insecure_hosts = ("localhost", "127.0.0.1", "0.0.0.0", "maas.aliyuncs.com")
        if any(h in config.base_url for h in _insecure_hosts):
            self._ssl_context = ssl._create_unverified_context()
        else:
            self._ssl_context = ssl.create_default_context()

    def supports_tools(self) -> bool:
        return True

    # ── URL 构造 ──

    def _build_url(self) -> str:
        base = self.config.base_url.rstrip("/")
        # 自动补全 /v1 前缀
        if "/v1" not in base:
            base += "/v1"
        return f"{base}/chat/completions"

    # ── 请求构造 ──

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.update(self.config.extra_headers)
        return headers

    def _sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """清洗消息列表，确保 content 字段不为 None/null。
        
        Ollama 及部分 OpenAI 兼容端点拒绝 content=null 的请求体（400），
        但 ChatEngine 在 tool_calls 场景下会将 assistant 消息的 content 置为 None。
        此处将 None 转为空字符串 ""，保留其他字段不变。
        """
        cleaned = []
        for m in messages:
            msg = dict(m)
            if msg.get("content") is None:
                msg["content"] = ""
            cleaned.append(msg)
        return cleaned

    def _build_payload(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        stream: bool = False,
        tool_choice: Optional[str] = None,
    ) -> dict:
        payload = {
            "model": self.config.model,
            "messages": self._sanitize_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        return payload

    # ── HTTP 请求 ──

    def _make_request(self, payload: dict, timeout: int = 600) -> dict:
        """发送 HTTP POST 请求并返回解析后的 JSON"""
        url = self._build_url()
        headers = self._build_headers()
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            
            # 检测 token 用尽错误
            is_no_token = self._check_no_token_error(e.code, error_body)
            if is_no_token:
                # 标记模型为失效
                try:
                    from opcclaw.core.model_status import mark_model_no_token
                    mark_model_no_token(self.config.model, self.config.name)
                except ImportError:
                    pass
                
                raise RuntimeError(
                    f"[{self.config.name}] Token 用尽或额度不足: {error_body[:300]}"
                )
            
            raise RuntimeError(
                f"[{self.config.name}] API error {e.code}: {error_body[:500]}"
            )
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"[{self.config.name}] 连接失败: {e.reason}\n"
                f"请检查: 1) 网络连接 2) base_url 是否正确 ({self.config.base_url})"
            )
        except Exception as e:
            raise RuntimeError(f"[{self.config.name}] 请求异常: {e}")
    
    def _check_no_token_error(self, code: int, error_body: str) -> bool:
        """
        检查是否为 token 用尽错误
        
        Args:
            code: HTTP 状态码
            error_body: 错误响应体
            
        Returns:
            True 表示 token 用尽
        """
        # HTTP 400 = 参数错误（如 max_tokens 超限），绝对不是额度问题
        if code == 400:
            return False
        
        # 检查状态码
        if code == 401:  # Unauthorized - 通常表示 token 失效
            return True
        if code == 403:  # Forbidden - 可能表示额度不足
            return True
        if code == 429:  # Too Many Requests - 速率限制
            return True
        
        # 检查错误消息中的关键字
        error_lower = error_body.lower()
        token_keywords = [
            "token",
            "quota",
            "额度",
            "余额不足",
            "credit",
            "insufficient",
            "exceed",
            "限制",
            "用尽",
        ]
        
        if any(kw in error_lower for kw in token_keywords):
            return True
        
        return False

    # ── 响应解析 ──

    def _parse_response(self, data: dict) -> LLMResponse:
        """解析 API JSON 响应 -> LLMResponse"""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "stop")

        # 文本内容 (可能为空字符串)
        content = message.get("content") or None

        # 工具调用
        tool_calls = None
        raw_tool_calls = message.get("tool_calls", [])
        if raw_tool_calls:
            parsed = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except (json.JSONDecodeError, TypeError):
                    args = {}
                parsed.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=args,
                ))
            if parsed:
                tool_calls = parsed

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            model=data.get("model", self.config.model),
            usage=data.get("usage", {}),
            is_tool_call=finish_reason == "tool_calls" or bool(tool_calls),
        )

    # ── 公开接口 ──

    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        token_saver_mode: str = "balanced",  # Token 节约模式
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """聊天接口，可选 Token 优化和强制工具调用
        
        对本地模型（如 Ollama）使用内部流式读取，防止大模型（35b+）生成长链推理时
        因 ollama 全量缓存导致 socket 超时。
        """
        is_local = self._is_local_provider()
        
        # 应用 Token 优化
        if token_saver_mode != "disabled":
            messages = optimize_messages(messages, mode=token_saver_mode)
        
        if is_local and not tools:
            # 本地模型走内部流式，逐 chunk 消费防止 socket timeout
            return self._chat_stream_accumulate(
                messages, tools, token_saver_mode, tool_choice
            )
        
        payload = self._build_payload(messages, tools, stream=False, tool_choice=tool_choice)
        data = self._make_request(payload)
        return self._parse_response(data)
    
    def _is_local_provider(self) -> bool:
        """检测是否为本地供应商（Ollama/localhost）"""
        try:
            return (
                self.config.name == "llama.cpp"
                or "ollama" in self.config.provider_type.lower()
                or "llama.cpp" in self.config.name.lower()
                or "localhost" in self.config.base_url
                or "127.0.0.1" in self.config.base_url
                or "8080" in self.config.base_url
            )
        except Exception:
            return False
    
    def _chat_stream_accumulate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        token_saver_mode: str = "balanced",
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """内部流式读取（逐 chunk 消费防止 socket timeout），
        聚合完整响应后以 LLMResponse 返回。"""
        import json as _json
        
        if token_saver_mode != "disabled":
            messages = optimize_messages(messages, mode=token_saver_mode)
        
        payload = self._build_payload(messages, tools, stream=True, tool_choice=tool_choice)
        url = self._build_url()
        headers = self._build_headers()
        data_bytes = _json.dumps(payload, ensure_ascii=False).encode("utf-8")
        
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        
        accumulated_content = ""
        accumulated_reasoning = ""
        model_name = ""
        usage = {}
        finish_reason = "stop"
        tool_calls_raw = []
        
        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=600) as resp:
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = _json.loads(data_str)
                    except _json.JSONDecodeError:
                        continue
                    
                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    if "content" in delta and delta["content"]:
                        accumulated_content += delta["content"]
                    if "reasoning_content" in delta and delta["reasoning_content"]:
                        accumulated_reasoning += delta["reasoning_content"]
                    if "tool_calls" in delta:
                        tool_calls_raw = delta["tool_calls"]
                    if choice.get("finish_reason"):
                        finish_reason = choice.get("finish_reason", "stop")
                    if chunk.get("model"):
                        model_name = chunk.get("model", "")
                    if chunk.get("usage"):
                        usage = chunk.get("usage", {})
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"[{self.config.name}] API error {e.code}: {error_body[:500]}"
            )
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"[{self.config.name}] 连接失败: {e.reason}\n"
                f"请检查: 1) 网络连接 2) base_url 是否正确 ({self.config.base_url})"
            )
        except Exception as e:
            raise RuntimeError(f"[{self.config.name}] 请求异常: {e}")
        
        # 构造返回
        parsed_tool_calls = None
        if tool_calls_raw:
            parsed = []
            for tc in tool_calls_raw:
                func = tc.get("function", {})
                try:
                    args = _json.loads(func.get("arguments", "{}"))
                except (_json.JSONDecodeError, TypeError):
                    args = {}
                parsed.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=args,
                ))
            if parsed:
                parsed_tool_calls = parsed
        
        return LLMResponse(
            content=accumulated_content or None,
            reasoning=accumulated_reasoning or None,
            tool_calls=parsed_tool_calls,
            finish_reason=finish_reason,
            model=model_name or self.config.model,
            usage=usage,
            is_tool_call=finish_reason == "tool_calls" or bool(parsed_tool_calls),
        )

    def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        token_saver_mode: str = "balanced",  # Token 节约模式
        tool_choice: Optional[str] = None,
    ) -> Iterator[LLMResponse]:
        """SSE 流式响应。工具调用时不流式, 降级为普通请求。"""
        
        # 如果带有工具, 工具调用结果通常不流式
        if tools:
            yield self.chat(messages, tools, token_saver_mode, tool_choice=tool_choice)
            return
        
        # 应用 Token 优化
        if token_saver_mode != "disabled":
            messages = optimize_messages(messages, mode=token_saver_mode)
        
        payload = self._build_payload(messages, tools=None, stream=True)
        url = self._build_url()
        headers = self._build_headers()
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        accumulated = ""
        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=600) as resp:
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # 去掉 "data: " 前缀
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        accumulated += delta["content"]
                        yield LLMResponse(
                            content=delta["content"],
                            model=chunk.get("model", ""),
                        )

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            yield LLMResponse(
                content=f"[Error {e.code}: {error_body[:300]}]"
            )
        except Exception as e:
            yield LLMResponse(content=f"[连接错误: {e}]")


# ═══════════════════════════════════════════
# 内置供应商模板 (25个)
# ═══════════════════════════════════════════

PROVIDER_TEMPLATES = {
    # ── 云端模型 ──
    "deepseek": ProviderConfig(
        name="DeepSeek",
        provider_type="openai_compatible",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        max_tokens=8192,              # DeepSeek-V3 最大输出 8K
        description="DeepSeek-V3 通用大模型, 性价比极高",
        available_models=["deepseek-chat", "deepseek-reasoner"],
    ),
    "deepseek_reasoner": ProviderConfig(
        name="DeepSeek Reasoner",
        provider_type="openai_compatible",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-reasoner",
        max_tokens=8192,              # DeepSeek-R1 最大输出 8K (推理 token 不计入)
        description="DeepSeek-R1 深度推理模型",
        available_models=["deepseek-chat", "deepseek-reasoner"],
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        provider_type="openai_compatible",
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
        max_tokens=16384,             # GPT-4o 最大输出 16K
        description="GPT-4o / GPT-4 / GPT-3.5 系列",
        available_models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"],
    ),
    "tongyi": ProviderConfig(
        name="通义千问",
        provider_type="openai_compatible",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        max_tokens=131072,            # Qwen3-235B 最大输出 128K, qwen-plus/turbo 为 8K
        description="阿里云通义千问 Qwen 系列",
        available_models=["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-235b-a22b", "qwen2.5-72b-instruct", "qwen2.5-32b-instruct", "qwen2.5-14b-instruct", "qwen2.5-7b-instruct"],
    ),
    "zhipu": ProviderConfig(
        name="智谱 GLM",
        provider_type="openai_compatible",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model="glm-4-plus",
        max_tokens=4096,              # GLM-4 系列最大输出 4K
        description="智谱 GLM-4 系列",
        available_models=["glm-4-plus", "glm-4-flash", "glm-4-air", "glm-4-long", "glm-4v-plus", "glm-4v-flash"],
    ),
    "moonshot": ProviderConfig(
        name="Moonshot",
        provider_type="openai_compatible",
        base_url="https://api.moonshot.cn/v1",
        model="moonshot-v1-8k",
        max_tokens=4096,              # Moonshot 最大输出约 4K
        description="月之暗面 Kimi / Moonshot",
        available_models=["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    ),
    "wenxin": ProviderConfig(
        name="百度文心 (千帆)",
        provider_type="openai_compatible",
        base_url="https://qianfan.baidubce.com/v2",
        model="ernie-4.0-8k",
        max_tokens=2048,              # ERNIE 系列最大输出 2K
        description="百度千帆大模型平台 - ERNIE 系列 [需 API Key + Secret Key 换取 access_token]",
        available_models=["ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-3.5-8k", "ernie-speed-8k", "ernie-lite-8k", "ernie-tiny-8k"],
    ),
    "xunfei": ProviderConfig(
        name="讯飞星火",
        provider_type="openai_compatible",
        base_url="https://spark-api-open.xf-yun.com/v1",
        model="4.0Ultra",
        max_tokens=8192,              # 星火 4.0 最大输出 8K
        description="讯飞星火认知大模型 [需 AppId + API Key + Secret]",
        available_models=["4.0Ultra", "generalv3.5", "generalv3", "spark-lite", "pro-128k", "max-32k"],
    ),
    "groq": ProviderConfig(
        name="Groq",
        provider_type="openai_compatible",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
        max_tokens=32768,             # Groq 最大输出 32K
        description="Groq LPU 高速推理",
        available_models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it", "deepseek-r1-distill-llama-70b"],
    ),
    "together": ProviderConfig(
        name="Together AI",
        provider_type="openai_compatible",
        base_url="https://api.together.xyz/v1",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        max_tokens=16384,             # Together 默认 16K，部分模型支持更高
        description="Together AI 多模型托管平台",
        available_models=["meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Llama-3.1-405B-Instruct-Turbo", "meta-llama/Llama-3.1-70B-Instruct-Turbo", "meta-llama/Llama-3.1-8B-Instruct-Turbo", "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "google/gemma-2-27b-it"],
    ),
    "openrouter": ProviderConfig(
        name="OpenRouter",
        provider_type="openai_compatible",
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-4o",
        max_tokens=131072,            # OpenRouter 取上限，实际由底层模型决定
        description="OpenRouter 多模型聚合网关",
        available_models=["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-sonnet-4-20250514", "google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-r1"],
    ),
    "siliconflow": ProviderConfig(
        name="SiliconFlow",
        provider_type="openai_compatible",
        base_url="https://api.siliconflow.cn/v1",
        model="deepseek-ai/DeepSeek-V3",
        max_tokens=16384,             # SiliconFlow 默认 16K
        description="硅基流动 多模型推理平台",
        available_models=["deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen2.5-32B-Instruct", "THUDM/glm-4-9b-chat", "meta-llama/Llama-3.3-70B-Instruct"],
    ),
    "mistral": ProviderConfig(
        name="Mistral AI",
        provider_type="openai_compatible",
        base_url="https://api.mistral.ai/v1",
        model="mistral-large-latest",
        max_tokens=131072,            # Mistral Large 最大输出 128K
        description="Mistral Large / Small / Codestral 系列",
        available_models=["mistral-large-latest", "mistral-small-latest", "codestral-latest", "mistral-saba"],
    ),
    "perplexity": ProviderConfig(
        name="Perplexity",
        provider_type="openai_compatible",
        base_url="https://api.perplexity.ai",
        model="sonar-pro",
        max_tokens=8192,              # Perplexity 最大输出 8K
        description="Perplexity Sonar 搜索增强模型 - 支持实时联网",
        available_models=["sonar-pro", "sonar", "sonar-reasoning"],
    ),
    "fireworks": ProviderConfig(
        name="Fireworks AI",
        provider_type="openai_compatible",
        base_url="https://api.fireworks.ai/inference/v1",
        model="accounts/fireworks/models/llama-v3p1-405b-instruct",
        max_tokens=16384,             # Fireworks 默认 16K
        description="Fireworks AI 高速推理 - Llama/Mixtral/DeepSeek 等",
        available_models=["accounts/fireworks/models/llama-v3p1-405b-instruct", "accounts/fireworks/models/llama-v3p1-70b-instruct", "accounts/fireworks/models/llama-v3p1-8b-instruct", "accounts/fireworks/models/mixtral-8x7b-instruct", "accounts/fireworks/models/deepseek-v3"],
    ),
    "cohere": ProviderConfig(
        name="Cohere",
        provider_type="openai_compatible",
        base_url="https://api.cohere.com/v1",
        model="command-r-plus",
        max_tokens=4096,              # Cohere 最大输出 4K
        description="Cohere Command R/R+ 企业级 RAG 模型",
        available_models=["command-r-plus", "command-r"],
    ),
    "minimax": ProviderConfig(
        name="MiniMax (海螺AI)",
        provider_type="openai_compatible",
        base_url="https://api.minimax.chat/v1",
        model="abab6.5s-chat",
        max_tokens=8192,              # MiniMax abab6.5 最大输出 8K
        description="MiniMax 海螺AI - ABAB 系列大模型",
        available_models=["abab6.5s-chat", "abab6.5-chat"],
    ),
    "stepfun": ProviderConfig(
        name="阶跃星辰 (StepFun)",
        provider_type="openai_compatible",
        base_url="https://api.stepfun.com/v1",
        model="step-2-16k",
        max_tokens=16384,             # Step-2 最大输出 16K
        description="阶跃星辰 Step 系列大模型",
        available_models=["step-2-16k", "step-1-8k", "step-1-32k", "step-1-128k", "step-1-flash"],
    ),
    # ── 本地模型 (Ollama / LM Studio / vLLM 等) ──
    "ollama": ProviderConfig(
        name="Ollama (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:11434/v1",
        model="qwen3.6:35b",
        max_tokens=131072,
        description="Ollama 本地推理服务 - 一键管理模型",
        available_models=[],  # 模型列表由 /api/tags 动态获取
    ),
    "lmstudio": ProviderConfig(
        name="LM Studio (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:1234/v1",
        model="local-model",
        max_tokens=131072,            # 本地模型取 128K
        description="LM Studio 本地推理服务 - 图形界面管理模型",
        available_models=["local-model"],
    ),
    "vllm": ProviderConfig(
        name="vLLM (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:8000/v1",
        model="default",
        max_tokens=131072,            # 本地模型取 128K，vLLM 启动参数控制
        description="vLLM 高性能推理引擎 - 适合生产环境",
        available_models=["default"],
    ),
    "llamacpp": ProviderConfig(
        name="llama.cpp (本地)",
        provider_type="openai_compatible",
        base_url="http://localhost:8080/v1",
        model="local",
        max_tokens=131072,
        description="llama.cpp server - 轻量 GGUF 模型推理",
        available_models=["local"],
    ),
    # ── 自定义 ──
    "custom": ProviderConfig(
        name="自定义 OpenAI 兼容",
        provider_type="openai_compatible",
        base_url="http://localhost:11434/v1",
        model="default",
        max_tokens=131072,            # 自定义端点取 128K，用户按需调整
        description="任意符合 OpenAI API 格式的端点",
        available_models=["default"],
    ),
"bailian": ProviderConfig(
        name="阿里云百炼",
        provider_type="openai_compatible",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        max_tokens=131072,            # 百炼同通义千问系，取 128K
        description="阿里云百炼 MaaS 平台 — Qwen/DeepSeek/Kimi 等云端模型",
        available_models=[
            # 通义千问系列
            "qwen-plus", "qwen-max", "qwen-turbo",
            "qwen-vl-plus", "qwen-vl-max", "qwen-vl-ocr",
            "qwen-audio-turbo", "qwen-mt-plus", "qwen-cv-plus",
            "qwen-math-plus", "qwen-code-plus", "qwen-coder-plus",
            "qwen-long", "qwen-text-embedding-v1", "qwen-text-embedding-v2",
            "qwen-text-embedding-v3",
            # 新一代模型
            "qwen2.5-72b-instruct", "qwen2.5-32b-instruct", "qwen2.5-14b-instruct", "qwen2.5-7b-instruct",
            "qwen2.5-1.5b-instruct", "qwen2.5-0.5b-instruct",
            "qwen3-235b-a22b", "qwen3-110b-a22b", "qwen3-64b-a22b",
            "qwen3.5-plus-2026-04-20", "qwen3.5-max-2026-04-20",
            "qwen3.6-27b", "qwen3.6-72b",
            # DeepSeek 系列
            "deepseek-v3-pro", "deepseek-v3-plus", "deepseek-v3-flash",
            "deepseek-v4-pro", "deepseek-v4-plus", "deepseek-v4-flash",
            "deepseek-r1", "deepseek-r1-distill-llama-70b", "deepseek-r1-distill-llama-8b",
            # Kimi 系列
            "kimi/kimi-k2.6", "kimi/kimi-k2.5", "kimi/kimi-k2",
            "kimi/kimi-k1.5", "kimi/kimi-k1", "kimi/kimi-k0",
            "kimi-k2-100k", "kimi-k2-128k", "kimi-k2-200k",
            # GLM 系列
            "glm-4-plus", "glm-4-flash", "glm-4-air", "glm-4-long",
            "glm-4v-plus", "glm-4v-flash", "glm-4v-air",
            "glm-4-alltools", "glm-4-alltools-flash",
            "glm-4-9b", "glm-4-9b-chat", "glm-4-0520",
            "glm-3-turbo", "glm-3-turbo-pro",
            # Llama 系列
            "llama-3.3-70b-instruct", "llama-3.1-405b-instruct", "llama-3.1-70b-instruct",
            "llama-3.1-8b-instruct", "llama-3.2-3b-instruct", "llama-3.2-1b-instruct",
            # 其他模型
            "gemma-2-27b-it", "gemma-2-9b-it", "gemma-2-2b-it",
            "mistral-large-2407", "mistral-nemo", "mistral-7b-instruct",
            "mixtral-8x7b-32768", "mixtral-8x22b-instruct",
            "phi-3-mini-128k-instruct", "phi-3-medium-128k-instruct",
            "qwen2-57b-a14b-instruct", "qwen2-72b-instruct",
            "yi-1.5-34b-chat", "yi-1.5-9b-chat", "yi-large",
            "baichuan2-13b-chat", "baichuan2-7b-chat",
            "internlm2_5-20b-chat", "internlm2_5-7b-chat",
            # 多模态
            "qwen-vl-max", "qwen-vl-plus", "qwen-vl-chat-v1",
            # 音频
            "qwen-audio-turbo", "funasr-resnet50-asr-zh",
            # 向量
            "text-embedding-v1", "text-embedding-v2", "text-embedding-v3",
            # 搜索
            "qwen-search-plus", "qwen-search-max",
        ],
    ),
}


# ═══════════════════════════════════════════
# 模型列表获取
# ═══════════════════════════════════════════

def list_all_providers() -> dict[str, dict]:
    """
    列出所有内置供应商的元数据。
    返回 {id: {name, is_local, needs_key, default_model, base_url, description}}
    供 UI 层直接使用，无需导入 ProviderConfig。
    """
    result = {}
    for key, cfg in PROVIDER_TEMPLATES.items():
        is_local = any(h in cfg.base_url for h in ("localhost", "127.0.0.1", "0.0.0.0"))
        result[key] = {
            "id": key,
            "name": cfg.name,
            "is_local": is_local,
            "needs_key": not is_local and key != "custom",
            "default_model": cfg.model,
            "base_url": cfg.base_url,
            "description": cfg.description,
        }
    return result


def get_available_models(base_url: str, api_key: str = "", timeout: int = 15) -> list[str]:
    """
    从 OpenAI 兼容端点获取可用模型列表。
    大多数云端平台都有几十到几百个模型，
    此函数列出所有可用模型供用户切换。

    Args:
        base_url: API 端点地址 (如 https://api.deepseek.com/v1)
        api_key: API Key
        timeout: 请求超时秒数

    Returns:
        模型 ID 列表 (按字母排序)

    Raises:
        RuntimeError: 网络错误或 API 返回异常

    Usage:
        models = get_available_models("https://dashscope.aliyuncs.com/compatible-mode/v1", api_key="sk-xxx")
        # ['qwen-max', 'qwen-plus', 'qwen-turbo', ...]
    """
    url = base_url.rstrip("/")
    if "/v1" not in url:
        url += "/v1"
    url += "/models"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        ctx = ssl.create_default_context()
        if any(h in base_url for h in ("localhost", "127.0.0.1", "0.0.0.0")):
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["id"] for m in data.get("data", [])]
            models.sort()
            return models
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"获取模型列表失败: {e}")


def batch_scan_platforms(providers: dict[str, dict], timeout: int = 15) -> dict[str, dict]:
    """
    批量探测多个平台的连通性、模型列表和测试对话。
    自动区分: 缺Key / Key无效(401) / 网络不通 / 成功。

    Args:
        providers: {platform_id: {"name":str, "base_url":str, "api_key":str, "model":str}}
        timeout: 请求超时(秒)

    Returns:
        {platform_id: {
            "status": "ok"|"no_key"|"invalid_key"|"network_error"|"http_error",
            "model_count": int,
            "models": list[str],         # 前5个示例
            "test_response": str,         # 测试回复
            "error": str,                 # 错误信息
            "http_code": int,             # HTTP状态码(如有)
        }}
    """
    import time
    results = {}

    for pid, info in providers.items():
        base_url = info.get("base_url", "").strip()
        api_key = info.get("api_key", "").strip()
        model = info.get("model", "").strip()
        name = info.get("name", pid)

        if not api_key:
            results[pid] = {"status": "no_key", "name": name,
                             "model_count": 0, "models": [],
                             "test_response": "", "error": "API Key not provided"}
            continue

        result = {"status": "unknown", "name": name,
                  "model_count": 0, "models": [],
                  "test_response": "", "error": ""}

        # 1) 获取模型列表
        try:
            models = get_available_models(base_url, api_key, timeout=timeout)
            result["model_count"] = len(models)
            result["models"] = models[:5]
            result["status"] = "ok"
        except RuntimeError as re:
            msg = str(re)
            if "401" in msg or "invalid_api_key" in msg.lower():
                result["status"] = "invalid_key"
                result["error"] = msg[:200]
            elif "403" in msg:
                result["status"] = "http_error"
                result["error"] = "403 Forbidden - check permissions"
            else:
                result["status"] = "http_error"
                result["error"] = msg[:200]
        except Exception as e:
            result["status"] = "network_error"
            result["error"] = str(e)[:200]

        # 2) 测试聊天 (仅当模型列表成功时)
        if result["status"] == "ok" and model:
            try:
                cfg = ProviderConfig(name=name, provider_type="openai_compatible",
                                     base_url=base_url, api_key=api_key, model=model)
                backend = BackendFactory.create(cfg)
                resp = backend.chat([{"role": "user", "content": "Hi"}], tools=None)
                result["test_response"] = (resp.content or "")[:100]
            except RuntimeError as re:
                result["test_response"] = f"[Error] {str(re)[:100]}"
            except Exception as e:
                result["test_response"] = f"[Error] {str(e)[:100]}"

        results[pid] = result
        time.sleep(0.2)  # 避免限流

    return results


# ═══════════════════════════════════════════
# 后端工厂
# ═══════════════════════════════════════════

class BackendFactory:
    """根据配置创建对应的 LLM 后端实例"""

    @staticmethod
    def create(config: ProviderConfig) -> BaseLLMBackend:
        pt = config.provider_type
        if pt == "openai_compatible":
            return OpenAICompatibleBackend(config)
        else:
            raise ValueError(
                f"不支持的供应商类型: {pt}\n"
                f"当前支持: openai_compatible (覆盖 OpenAI/DeepSeek/Ollama 等)"
            )

    @staticmethod
    def from_template(
        template_name: str,
        api_key: str = "",
        model: str = "",
        base_url: str = "",
    ) -> BaseLLMBackend:
        """
        从内置模板创建后端。

        用法:
            be = BackendFactory.from_template("deepseek", api_key="sk-xxx")
            be = BackendFactory.from_template("ollama")  # 无需 api_key
            be = BackendFactory.from_template("ollama", model="llama3:8b")
        """
        template = PROVIDER_TEMPLATES.get(template_name)
        if not template:
            available = ", ".join(PROVIDER_TEMPLATES.keys())
            raise ValueError(
                f"未知模板: '{template_name}'\n可用: {available}"
            )

        config = ProviderConfig(
            name=template.name,
            provider_type=template.provider_type,
            base_url=base_url or template.base_url,
            api_key=api_key or template.api_key,
            model=model or template.model,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            extra_headers=dict(template.extra_headers),
            description=template.description,
        )
        return BackendFactory.create(config)

    @staticmethod
    def from_dict(config_dict: dict) -> BaseLLMBackend:
        """从字典恢复后端 (用于设置持久化)"""
        # 过滤掉不在 ProviderConfig 中的键
        valid_keys = {f.name for f in ProviderConfig.__dataclass_fields__.values()}
        filtered = {k: v for k, v in config_dict.items() if k in valid_keys}
        config = ProviderConfig(**filtered)
        return BackendFactory.create(config)

    @staticmethod
    def list_templates() -> list[dict]:
        """列出所有可用供应商模板"""
        result = []
        for key, cfg in PROVIDER_TEMPLATES.items():
            is_local = any(h in cfg.base_url for h in ("localhost", "127.0.0.1", "0.0.0.0"))
            result.append({
                "id": key,
                "name": cfg.name,
                "model": cfg.model,
                "description": cfg.description,
                "local": is_local,
                "needs_api_key": not is_local and key != "custom",
            })
        return result


# ═══════════════════════════════════════════
# 便捷 API
# ═══════════════════════════════════════════

def create_backend(
    provider: str = "deepseek",
    api_key: str = "",
    model: str = "",
    base_url: str = "",
    temperature: float = 0.7,
    max_tokens: int = 262144,) -> BaseLLMBackend:
    """
    一行创建 LLM 后端。

    用法:
        backend = create_backend("deepseek", api_key="sk-xxx")
        backend = create_backend("ollama", model="qwen2.5:14b")
        backend = create_backend("custom", base_url="http://myserver:8000/v1", model="my-model")
    """
    try:
        return BackendFactory.from_template(provider, api_key, model, base_url)
    except ValueError:
        # 如果不是内置模板, 当作自定义 OpenAI 兼容端点
        cfg = ProviderConfig(
            name=provider,
            provider_type="openai_compatible",
            base_url=base_url or "http://localhost:11434/v1",
            api_key=api_key,
            model=model or "default",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return BackendFactory.create(cfg)
