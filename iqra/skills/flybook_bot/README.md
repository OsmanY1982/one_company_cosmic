# Iqra HTTP API Server - 浏览器自动化

## 功能说明

增强了原有的 flybook_bot server，添加了以下功能：

### API 端点

1. **POST /chat** - AI 对话（支持工具调用）
   - 集成 Iqra 核心引擎
   - 支持多轮工具调用
   - 可调用浏览器操作工具

2. **POST /browser/action** - 直接浏览器操作
   - open: 打开网页
   - click: 点击元素
   - fill: 填充输入框
   - screenshot: 截图
   - get_content: 获取页面内容
   - execute_js: 执行 JavaScript
   - close: 关闭浏览器

3. **GET /health** - 健康检查

4. **GET /tools** - 列出所有可用工具

5. **POST /feishu/webhook** - 飞书消息 Webhook（保留原有功能）

## 安装依赖

### 1. 安装 Playwright

```bash
pip install playwright
playwright install chromium
```

### 2. 安装 Flask（如果未安装）

```bash
pip install flask
```

### 3. 安装 Iqra 依赖

```bash
cd D:/one_company_desktop/iqra
pip install -r requirements.txt  # 如果有的话
```

## 启动服务器

```bash
python D:/one_company_desktop/iqra/skills/flybook_bot/server.py
```

启动后监听：`http://127.0.0.1:8080`

## 使用示例

### 1. 健康检查

```bash
curl http://127.0.0.1:8080/health
```

### 2. AI 对话

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，请介绍一下你自己",
    "clear_history": true
  }'
```

### 3. AI 对话 + 浏览器操作

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请打开 https://www.bing.com 并获取页面标题",
    "clear_history": true
  }'
```

### 4. 直接浏览器操作

#### 打开网页

```bash
curl -X POST http://127.0.0.1:8080/browser/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "open",
    "params": {
      "url": "https://www.bing.com",
      "headless": true
    }
  }'
```

#### 获取页面内容

```bash
curl -X POST http://127.0.0.1:8080/browser/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_content",
    "params": {}
  }'
```

#### 点击元素

```bash
curl -X POST http://127.0.0.1:8080/browser/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "click",
    "params": {
      "selector": "#search_form"
    }
  }'
```

#### 填充输入框

```bash
curl -X POST http://127.0.0.1:8080/browser/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "fill",
    "params": {
      "selector": "input[name=q]",
      "value": "AI 助手"
    }
  }'
```

#### 截图

```bash
curl -X POST http://127.0.0.1:8080/browser/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "screenshot",
    "params": {
      "path": "D:/screenshots/test.png"
    }
  }'
```

#### 执行 JavaScript

```bash
curl -X POST http://127.0.0.1:8080/browser/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "execute_js",
    "params": {
      "javascript": "document.title"
    }
  }'
```

#### 关闭浏览器

```bash
curl -X POST http://127.0.0.1:8080/browser/action \
  -H "Content-Type: application/json" \
  -d '{
    "action": "close",
    "params": {}
  }'
```

### 5. 查看可用工具

```bash
curl http://127.0.0.1:8080/tools
```

## 运行测试

```bash
python D:/one_company_desktop/iqra/skills/flybook_bot/test_server.py
```

测试项目：
1. ✅ 健康检查
2. ✅ 基础 AI 对话
3. ✅ 工具列表
4. ✅ 直接浏览器操作
5. ✅ AI 对话 + 浏览器

## CSS 选择器示例

浏览器操作使用 CSS 选择器定位元素：

| 选择器 | 说明 | 示例 |
|--------|------|------|
| ID 选择器 | 通过元素 ID 定位 | `#login-btn` |
| 类选择器 | 通过类名定位 | `.submit-button` |
| 标签选择器 | 通过标签名定位 | `input`, `button`, `a` |
| 属性选择器 | 通过属性定位 | `input[name=username]`, `a[href*='login']` |
| 层级选择器 | 通过父子关系定位 | `form input`, `div > button` |
| 伪类选择器 | 通过状态定位 | `a:first-child`, `input:focus` |

### 实用示例

```css
/* 登录按钮 */
#login-btn
button[type="submit"]
.form-submit

/* 输入框 */
input[name=username]
input[type=email]
#search-input

/* 链接 */
a[href*='product']
.nav-link
.menu a:first-child

/* 表单 */
form#login-form
.form-container input

/* 复杂选择器 */
div.product-list > div.item:nth-child(2) button.buy-btn
form input[type="submit"]:disabled
```

## 集成到 Iqra 主程序

在 Iqra 主程序中使用 HTTP API：

```python
import requests

BASE_URL = "http://127.0.0.1:8080"

# 1. AI 对话
def chat_with_ai(message):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": message, "clear_history": False}
    )
    return response.json()

# 2. 浏览器操作
def open_website(url):
    response = requests.post(
        f"{BASE_URL}/browser/action",
        json={"action": "open", "params": {"url": url}}
    )
    return response.json()

def click_element(selector):
    response = requests.post(
        f"{BASE_URL}/browser/action",
        json={"action": "click", "params": {"selector": selector}}
    )
    return response.json()

# 使用示例
if __name__ == '__main__':
    # 打开网页
    result = open_website("https://www.bing.com")
    print(f"打开网页：{result}")
    
    # AI 对话
    response = chat_with_ai("帮我搜索最新的 AI 新闻")
    print(f"AI 回复：{response['response']}")
```

## 注意事项

1. **首次运行**需要安装 Playwright 和浏览器：
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **浏览器模式**：
   - `headless=true`: 无头模式（后台运行，不可见）
   - `headless=false`: 可见模式（可以看到浏览器窗口）

3. **超时设置**：
   - 打开网页：30 秒
   - 点击/填充：5 秒
   - AI 对话：根据模型响应时间

4. **资源占用**：
   - 浏览器实例会占用内存（约 100-200MB）
   - 使用完毕后建议调用 `close` 关闭

5. **并发**：
   - 当前版本使用单例浏览器实例
   - 不支持多用户并发操作浏览器

## 故障排除

### 问题 1: 浏览器无法启动

```
Error: playwright not installed
```

**解决**: 安装 Playwright
```bash
pip install playwright
playwright install chromium
```

### 问题 2: 连接被拒绝

```
ConnectionRefusedError: [WinError 10061]
```

**解决**: 确保服务器正在运行
```bash
python D:/one_company_desktop/iqra/skills/flybook_bot/server.py
```

### 问题 3: 页面加载超时

```
TimeoutError: Navigation timeout exceeded
```

**解决**: 
- 检查网络连接
- 增加 timeout 参数（需要修改代码）
- 使用 `wait_until="domcontentloaded"` 代替`networkidle`

### 问题 4: 元素找不到

```
Error: Element not found: #login-btn
```

**解决**:
- 检查 CSS 选择器是否正确
- 确认页面已完全加载
- 使用 `get_content` 查看页面结构

## 更新日志

### v2.0 - 2026-05-14
- ✅ 添加 `/chat` 端点，支持 AI 对话
- ✅ 集成 Iqra 核心引擎
- ✅ 添加浏览器自动化工具（7 个）
- ✅ 添加 `/browser/action` 端点
- ✅ 添加 `/health` 健康检查
- ✅ 添加 `/tools` 工具列表
- ✅ 保留原有 `/feishu/webhook` 功能
- ✅ 添加测试套件

### v1.0 - 早期版本
- 仅支持 `/feishu/webhook`
