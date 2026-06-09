"""
统一数据层 — 路径管理 + 数据库初始化
从旧项目 one_company_desktop 提取并精简
"""
import os, sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "log")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# DB 路径
ORDER_DB = os.path.join(DATA_DIR, "order.db")
PRODUCT_DB = os.path.join(DATA_DIR, "product.db")
CUSTOMER_DB = os.path.join(DATA_DIR, "customer.db")
FINANCE_DB = os.path.join(DATA_DIR, "finance.db")
MEMBER_DB = os.path.join(DATA_DIR, "member.db")
USERS_DB = os.path.join(DATA_DIR, "users.db")


def init_all_dbs():
    """初始化所有业务表"""
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