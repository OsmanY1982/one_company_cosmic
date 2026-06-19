# `core/operation_log.py`

> 路径：`core/operation_log.py` | 行数：81


---


```python
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime
from core.paths import DATA_DIR

LOG_DB = os.path.join(DATA_DIR, "operation_log.db")

def _ensure_db():
    os.makedirs(os.path.dirname(LOG_DB), exist_ok=True)
    conn = sqlite3.connect(LOG_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            module TEXT,
            detail TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

_ensure_db()

def log_action(username: str, action: str, module: str = "", detail: str = ""):
    try:
        conn = sqlite3.connect(LOG_DB)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO operation_logs (username, action, module, detail) VALUES (?, ?, ?, ?)",
            (username, action, module, detail)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"日志记录失败: {e}")

def get_logs(username=None, module=None, limit=200):
    try:
        conn = sqlite3.connect(LOG_DB)
        cursor = conn.cursor()
        
        conditions = []
        params = []
        if username:
            conditions.append("username = ?")
            params.append(username)
        if module:
            conditions.append("module = ?")
            params.append(module)
        
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT id, username, action, module, detail, created_at FROM operation_logs {where} ORDER BY id DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"查询日志失败: {e}")
        return []

def clear_old_logs(days=30):
    try:
        conn = sqlite3.connect(LOG_DB)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM operation_logs WHERE created_at < datetime('now', '-' || ? || ' days')",
            (days,)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"清理日志失败: {e}")
        return 0

```
