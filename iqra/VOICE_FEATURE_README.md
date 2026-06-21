# 语音功能集成说明

## 功能概述

Iqra 已经集成了语音识别(STT)和语音合成(TTS)功能，提供以下特性：

- 🔊 **语音输入**：点击语音按钮进行语音输入
- 🔋 **语音播报**：开关控制AI回复的语音播报
- 💬 **消息朗读**：在消息气泡中点击"朗读"按钮

## 依赖安装

### 必需依赖

```bash
# 安装语音识别依赖
pip install speech_recognition

# 安装语音合成依赖
pip install pyttsx3

# 安装音频处理依赖
pip install sounddevice
pip install numpy
```

### 可选依赖

```bash
# 替代语音合成（Edge TTS）
pip install edge-tts

# 本地语音识别（Whisper）
pip install openai-whisper
```

## 使用方法

### 语音输入
1. 点击输入框右侧的语音按钮（🎤）
2. 当按钮变成红色时，开始说话
3. 语音识别结果将自动填入输入框

### 语音播报
1. 默认开启语音播报
2. 点击音响按钮（🔊）可以开/关播报
3. AI的回复将自动进行语音播报

### 消息朗读
1. 在AI消息的操作按钮行中
2. 点击"🔊 朗读"按钮
3. 立即朗读当前消息

## 测试

运行测试脚本检查语音功能状态：

```bash
python test_voice_integration.py
```

## 常见问题

### 语音识别失败
- 确认安装了 `speech_recognition`
- 检查系统音频设备是否正常
- 确认微信权限已授予

### 语音播报失败
- 确认安装了 `pyttsx3` 或 `edge-tts`
- 检查系统音频输出是否正常
- 试试更换不同的TTS引擎

### 依赖安装失败
- 尝试使用虚拟环境
- 使用 `pip install --upgrade pip` 更新pip
- 检查Python版本兼容性