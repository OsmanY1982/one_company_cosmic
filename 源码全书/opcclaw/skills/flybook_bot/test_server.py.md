# `opcclaw/skills/flybook_bot/test_server.py`

> 路径：`opcclaw/skills/flybook_bot/test_server.py` | 行数：276


---


```python
"""
测试 OPCclaw HTTP API Server
============================

测试用例:
1. 健康检查
2. AI 对话（不带浏览器）
3. AI 对话（带浏览器操作）
4. 直接浏览器操作
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8080"


def test_health():
    """测试健康检查"""
    print("\n" + "=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码：{response.status_code}")
    print(f"响应：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.status_code == 200


def test_chat_basic():
    """测试基础对话"""
    print("\n" + "=" * 60)
    print("测试 2: 基础 AI 对话")
    print("=" * 60)
    
    payload = {
        "message": "你好，请介绍一下你自己",
        "clear_history": True
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码：{response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"AI 回复：{result.get('response')}")
        print(f"执行时间：{result.get('execution_time')}秒")
    else:
        print(f"错误：{result.get('error')}")
    
    return response.status_code == 200 and result.get('success')


def test_chat_with_browser():
    """测试带浏览器操作的对话"""
    print("\n" + "=" * 60)
    print("测试 3: AI 对话 + 浏览器操作")
    print("=" * 60)
    
    payload = {
        "message": "请打开 https://www.bing.com 并获取页面标题",
        "clear_history": True
    }
    
    print(f"发送请求...")
    start = time.time()
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    elapsed = time.time() - start
    print(f"状态码：{response.status_code}")
    print(f"耗时：{elapsed:.2f}秒")
    
    result = response.json()
    
    if result.get('success'):
        print(f"AI 回复：{result.get('response')}")
        
        tool_calls = result.get('tool_calls', [])
        if tool_calls:
            print(f"\n工具调用记录:")
            for tc in tool_calls:
                print(f"  - {tc}")
    else:
        print(f"错误：{result.get('error')}")
        if 'traceback' in result:
            print(f"堆栈：{result['traceback'][:500]}")
    
    return response.status_code == 200


def test_browser_direct():
    """测试直接浏览器操作"""
    print("\n" + "=" * 60)
    print("测试 4: 直接浏览器操作")
    print("=" * 60)
    
    # 1. 打开网页
    print("\n步骤 1: 打开 Bing")
    payload = {
        "action": "open",
        "params": {
            "url": "https://www.bing.com",
            "headless": True
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/browser/action",
        json=payload,
        timeout=30
    )
    
    print(f"状态码：{response.status_code}")
    result = response.json()
    print(f"结果：{json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if not result.get('success'):
        print("⚠️  浏览器操作失败，跳过后续测试")
        return False
    
    time.sleep(1)
    
    # 2. 获取页面内容
    print("\n步骤 2: 获取页面内容")
    payload = {
        "action": "get_content",
        "params": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/browser/action",
        json=payload,
        timeout=30
    )
    
    print(f"状态码：{response.status_code}")
    result = response.json()
    print(f"结果：{json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('success'):
        page_info = result.get('result', {})
        print(f"页面标题：{page_info.get('title')}")
        print(f"页面 URL: {page_info.get('url')}")
    
    time.sleep(1)
    
    # 3. 截图
    print("\n步骤 3: 截图")
    payload = {
        "action": "screenshot",
        "params": {
            "path": "D:/one_company_desktop/opcclaw/logs/test_screenshot.png"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/browser/action",
        json=payload,
        timeout=30
    )
    
    print(f"状态码：{response.status_code}")
    result = response.json()
    print(f"结果：{json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('success'):
        print(f"截图路径：{result.get('result', {}).get('path')}")
    
    time.sleep(1)
    
    # 4. 关闭浏览器
    print("\n步骤 4: 关闭浏览器")
    payload = {
        "action": "close",
        "params": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/browser/action",
        json=payload,
        timeout=30
    )
    
    print(f"状态码：{response.status_code}")
    result = response.json()
    print(f"结果：{json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return response.status_code == 200


def test_list_tools():
    """测试工具列表"""
    print("\n" + "=" * 60)
    print("测试 5: 工具列表")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/tools")
    print(f"状态码：{response.status_code}")
    
    result = response.json()
    if result.get('success'):
        tools = result.get('tools', [])
        print(f"可用工具数量：{len(tools)}")
        
        # 检查是否有浏览器工具
        browser_tools = [t for t in tools if 'browser' in t.get('function', {}).get('name', '')]
        print(f"浏览器工具：{len(browser_tools)} 个")
        for tool in browser_tools:
            func = tool.get('function', {})
            print(f"  - {func.get('name')}: {func.get('description', '')[:50]}")
    
    return response.status_code == 200


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("OPCclaw HTTP API Server 测试套件")
    print("🚀" * 30)
    
    # 检查服务器是否运行
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ 服务器已就绪")
    except requests.exceptions.ConnectionError:
        print("❌ 服务器未运行！请先启动服务器:")
        print("   python D:/one_company_desktop/opcclaw/skills/flybook_bot/server.py")
        return
    except Exception as e:
        print(f"❌ 连接错误：{e}")
        return
    
    results = []
    
    # 运行测试
    results.append(("健康检查", test_health()))
    results.append(("基础对话", test_chat_basic()))
    results.append(("工具列表", test_list_tools()))
    results.append(("浏览器直接操作", test_browser_direct()))
    results.append(("AI 对话 + 浏览器", test_chat_with_browser()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")


if __name__ == '__main__':
    main()

```
