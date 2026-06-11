---
name: smart_memory
description: "智能记忆系统：用户画像管理、学习特征提取、个性化适配、偏好快照/回滚"
version: "1.0"
emoji: "🧠"
tools: [read, write]
---

# Smart Memory Skill

## 简介

OPCclaw 智能记忆技能 - 基于 HERMES 架构的分层记忆系统

## 能力

- 用户画像管理
- 学习特征提取
- 个性化内容适配
- 偏好档案快照/回滚
- 应用边界检查
- 记忆写回路由

## 使用方式

### 基础操作

```python
from core.smart_memory import SmartMemory

# 创建实例
sm = SmartMemory()

# 更新用户画像
sm.update_user_profile({
    "basic_info": {"name": "用户名"},
    "work_context": {"role": "开发者"}
})

# 记录反馈
sm.record_accepted_suggestion("建议内容", "原因")
sm.record_rejected_suggestion("建议内容", "原因")
```

### 偏好档案管理

```python
# 更新偏好
sm.update_preference_profile({
    "writing_style": {"tone": "casual", "formality": "low"},
    "interaction": {"default_mode": "interactive"}
})

# 创建快照
snapshot = sm.create_snapshot("before-change")

# 回滚
sm.rollback_preference(snapshot["snapshot_id"])

# 冻结/解冻学习
sm.freeze_learning("临时禁用个性化")
sm.unfreeze_learning()
```

### 记忆写回路由

```python
# 短期态 - 不写入长期记忆
result = sm.route_memory_writeback("shortterm", {"data": "临时数据"})

# 项目态 - 写入项目文件
result = sm.route_memory_writeback("project", {"data": "项目数据"}, "project/memory.json")

# 长期态 - 更新检索画像
result = sm.route_memory_writeback("longterm", {
    "stable_domains": ["Python", "PyQt5"],
    "effective_query_patterns": ["如何...", "怎么..."]
})
```

### 内容适配

```python
# 适配内容
result = sm.adapt_content("原始内容", {"content_type": "general"})
print(result["content"])  # 适配后内容
print(result["logs"])     # 适配日志
```

### 边界检查

```python
# 检查应用边界
boundary = sm.check_application_boundary("内容", {"content_type": "code"})
if boundary["warnings"]:
    print("警告:", boundary["warnings"])
```

## 配置选项

```python
sm = SmartMemory(options={
    "enabled": True,              # 启用记忆系统
    "profile_isolation": True,    # 用户画像隔离
    "learning_rate": 0.1,         # 学习率
    "memory_retention_days": 90,  # 记忆保留天数
    "profile_id": "custom-id"     # 自定义画像ID
})
```

## 文件位置

- 主记忆: `data/opcclaw/smart_memory/memory.json`
- 偏好档案: `data/opcclaw/smart_memory/preferences/user-preference-profile.json`
- 快照: `data/opcclaw/smart_memory/snapshots/`
- 会话状态: `data/opcclaw/smart_memory/session_state/`

## 向后兼容

使用 SmartMemoryStore 同时兼容旧版 MemoryStore API:

```python
from core.smart_memory_adapter import SmartMemoryStore

store = SmartMemoryStore()

# 旧版 API
store.save_session(messages)
store.save_fact("事实")

# 新增 API
store.learn_from_interaction(user_msg, assistant_msg, "positive")
context = store.get_personalized_context()
```
