# `core/data.py`

> 路径：`core/data.py` | 行数：193


---


```python
"""
统一数据层 — 路径管理 + 数据库初始化 + 版本迁移
从旧项目 one_company_desktop 提取并精简
"""
import os, sqlite3, logging
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "log")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 当前 schema 版本号（递增）
SCHEMA_VERSION = 1

# DB 路径
ORDER_DB = os.path.join(DATA_DIR, "order.db")
PRODUCT_DB = os.path.join(DATA_DIR, "product.db")
CUSTOMER_DB = os.path.join(DATA_DIR, "customer.db")
FINANCE_DB = os.path.join(DATA_DIR, "finance.db")
MEMBER_DB = os.path.join(DATA_DIR, "member.db")
USERS_DB = os.path.join(DATA_DIR, "users.db")

# 迁移日志
_migration_log = os.path.join(LOG_DIR, "migration.log")

def _log_migration(msg):
    try:
        with open(_migration_log, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def _ensure_schema_version(conn, db_path):
    """为数据库创建 _schema_version 表并检查/写入版本号"""
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS _schema_version (
        id INTEGER PRIMARY KEY CHECK (id=1),
        version INTEGER NOT NULL,
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    row = c.execute("SELECT version FROM _schema_version WHERE id=1").fetchone()
    if row is None:
        c.execute("INSERT INTO _schema_version (id, version) VALUES (1, ?)", (SCHEMA_VERSION,))
        _log_migration(f"{db_path}: 初始化 schema v{SCHEMA_VERSION}")
    else:
        old_ver = row[0]
        if old_ver < SCHEMA_VERSION:
            # 未来在此处添加迁移脚本
            c.execute("UPDATE _schema_version SET version=?, updated_at=datetime('now','localtime') WHERE id=1",
                      (SCHEMA_VERSION,))
            _log_migration(f"{db_path}: 升级 schema v{old_ver} → v{SCHEMA_VERSION}")


def init_all_dbs():
    """初始化所有业务表（含 schema 版本管理）"""
    # orders
    conn = sqlite3.connect(ORDER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        product_name TEXT,
        quantity INTEGER DEFAULT 1,
        unit_price REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        status TEXT DEFAULT '已完成',
        note TEXT,
        payment_method TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    _ensure_schema_version(conn, ORDER_DB)
    conn.commit()
    conn.close()

    # products
    conn = sqlite3.connect(PRODUCT_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT '',
        price REAL DEFAULT 0,
        cost REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        unit TEXT DEFAULT '个',
        description TEXT DEFAULT '',
        status TEXT DEFAULT '在售',
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    _ensure_schema_version(conn, PRODUCT_DB)
    conn.commit()
    conn.close()

    # customers
    conn = sqlite3.connect(CUSTOMER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        company TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT DEFAULT '',
        level TEXT DEFAULT '普通',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    _ensure_schema_version(conn, CUSTOMER_DB)
    conn.commit()
    conn.close()

    # finance
    conn = sqlite3.connect(FINANCE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        category TEXT DEFAULT '',
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        description TEXT DEFAULT '',
        order_no TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    _ensure_schema_version(conn, FINANCE_DB)
    conn.commit()
    conn.close()

    # member
    conn = sqlite3.connect(MEMBER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS member (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        level TEXT DEFAULT 'TRIAL',
        points INTEGER DEFAULT 0,
        rights TEXT DEFAULT '',
        vip_expire TEXT DEFAULT '',
        status TEXT DEFAULT '激活',
        membership_type TEXT DEFAULT 'trial',
        membership_price REAL DEFAULT 0,
        membership_expire TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    # 兼容旧表：尝试添加新字段
    for col, col_type in [("membership_type", "TEXT DEFAULT 'trial'"),
                           ("membership_price", "REAL DEFAULT 0"),
                           ("membership_expire", "TEXT DEFAULT ''")]:
        try:
            c.execute(f"ALTER TABLE member ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass  # 字段已存在
    _ensure_schema_version(conn, MEMBER_DB)
    conn.commit()
    conn.close()

    # users (for auth)
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        license_type TEXT DEFAULT 'TRIAL',
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        membership_type TEXT DEFAULT 'TRIAL',
        activated_at TEXT,
        expires_at TEXT,
        activation_code TEXT
    )''')
    _ensure_schema_version(conn, USERS_DB)
    conn.commit()

    # 确保 admin 存在
    c.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password, license_type) VALUES (?, ?, ?)',
                  ('admin', 'admin', 'VIP'))
        c.execute('INSERT OR IGNORE INTO user_memberships (username, membership_type, activated_at) VALUES (?, ?, ?)',
                  ('admin', 'VIP', '2024-01-01 00:00:00'))
    conn.commit()
    conn.close()
```
