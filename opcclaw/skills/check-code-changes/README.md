---
named: check-code-changes
description: Check for code changes in the repository and report the results.
---

# 检查代码变更

## 任务描述
此技能用于定期检查项目代码库中的更改，并报告结果。

## 工具设置
使用 `search_files` 工具来查找文件变更。

## 任务逻辑
1. 检查指定目录下的所有文件是否有变更。
2. 如果有变更，则报告这些变更。
3. 如果没有变更，则通知用户当前没有新的代码变更。

## 实现
```python
from hermes_tools import search_files, terminal

def run():
    changes = search_files(r'^.*\.py$', target='files')
    if changes['matches']:
        print('发现变更文件：')
        for match in changes['matches']:
            print(f'- {match}')
    else:
        print('当前没有新的代码变更。')

if __name__ == '__main__':
    run()
```
