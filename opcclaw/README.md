# OPCclaw — 一人公司 AI 助手

> 基于 PyQt5 的桌面 AI 助手，支持多供应商 LLM + 工具调用 + 技能系统

## ✨ 功能

- **💬 智能对话** — 流式聊天，多轮对话，上下文记忆
- **🔧 工具调用** — 文件读写、代码执行、网页搜索等 60+ 工具
- **🤖 多供应商** — DeepSeek / OpenAI / 通义千问 / 智谱 GLM / Moonshot 等 25+ 平台
- **📚 技能系统** — 按需加载技能，自动匹配相关技能
- **🧠 记忆系统** — 会话持久化，智能记忆，长期偏好
- **🔐 安全存储** — API Key 加密存储，路径安全检查
- **☁️ 云端同步** — Supabase 数据同步（可选）
- **🎤 语音功能** — TTS 语音合成，语音输入（可选）
- **🖥️ 本地模型** — Ollama / LM Studio 连接

## 📁 项目结构

```
opcclaw/
├── main.py              # 启动入口
├── modules/
│   ├── chat_window.py   # 主窗口 UI
│   └── voice_manager.py # 语音管理
├── core/
│   ├── llm_backend.py   # LLM 多供应商统一接口
│   ├── chat_engine.py   # 对话引擎（工具调用循环）
│   ├── tool_registry.py # 工具注册表
│   ├── skill_loader.py  # 技能加载器
│   ├── memory_store.py  # 会话存储
│   ├── smart_memory.py  # 智能记忆
│   ├── token_saver.py   # Token 优化
│   ├── secure_storage.py# 安全存储
│   └── ...              # 其他核心模块
├── tools/               # 工具实现（60+ 工具）
├── skills/              # 技能定义（SKILL.md）
├── plugins/             # 插件系统
├── data/                # 运行时数据
└── logs/                # 日志文件
```

## 🚀 启动

```bash
# 双击运行
start_opcclaw.bat

# 或命令行
python main.py
```

## ⚙️ 配置

配置文件：`data/opcclaw_config.json`

```json
{
  "active_provider_id": "阿里云百炼",
  "cloud_providers": {
    "阿里云百炼": {
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model": "qwen3.7-max"
    }
  }
}
```

## 📋 依赖

- Python 3.8+
- PyQt5
- requests（可选，工具需要）
- selenium（可选，网页渲染）

## 📝 License

MIT
