# 飞书个人聊天机器人创建指南

## 步骤1：打开飞书App
- 打开手机上的飞书App
- 进入您的个人聊天界面（与自己对话）

## 步骤2：添加机器人
1. 点击右下角「+」按钮
2. 选择「添加机器人」
3. 选择「自定义机器人」
4. 填写机器人名称（如：AI助手）
5. 设置机器人头像（可选）
6. 点击「创建」

## 步骤3：获取Webhook URL
1. 创建成功后，系统会自动弹出一个对话框
2. 点击「复制链接」按钮
3. 将URL粘贴到 `/d/one_company_desktop/iqra/skills/flybook_bot/config.py` 文件中

## 步骤4：测试连接
```python
from flybook_bot.flybook_skill import send_flybook_message
send_flybook_message("测试消息：机器人已成功连接！")
```

## 注意事项
- 个人聊天机器人仅您自己可见
- 消息不会通知其他成员
- 可用于个人提醒、日程同步等场景
- 推荐使用企业账号创建，避免个人账号风险