# `opcclaw/init_db.py`

> 路径：`opcclaw/init_db.py` | 行数：180


---


```python
import sqlite3
import os

# 数据库路径（基于项目根目录的相对路径，跨平台兼容）
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sync", "local.db")

# 确保目录存在
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# 连接数据库
conn = sqlite3.connect(db_path)

# 创建表的SQL语句
tables = {
    'products': '''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specs TEXT,
            category TEXT,
            unit_price REAL,
            stock INTEGER,
            status TEXT,
            note TEXT,
            created_at TEXT
        )
    ''',
    'orders': '''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT,
            customer TEXT,
            product TEXT,
            amount REAL,
            quantity INTEGER,
            status TEXT,
            created_at TEXT
        )
    ''',
    'customers': '''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            company TEXT,
            note TEXT,
            created_at TEXT
        )
    ''',
    'finance': '''
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            category TEXT,
            amount REAL,
            description TEXT,
            order_no TEXT,
            date TEXT,
            created_at TEXT
        )
    ''',
    'staff': '''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            position TEXT,
            department TEXT,
            salary REAL,
            status TEXT,
            created_at TEXT
        )
    ''',
    'wallet': '''
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            balance REAL,
            frozen_amount REAL,
            total_income REAL,
            total_withdraw REAL,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''',
    'wallet_transactions': '''
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER,
            type TEXT,
            amount REAL,
            balance_after REAL,
            description TEXT,
            related_id TEXT,
            created_at TEXT
        )
    ''',
    'distribution_links': '''
        CREATE TABLE IF NOT EXISTS distribution_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            code TEXT,
            url TEXT,
            click_count INTEGER,
            register_count INTEGER,
            total_commission REAL,
            status TEXT,
            created_at TEXT
        )
    ''',
    'commissions': '''
        CREATE TABLE IF NOT EXISTS commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            from_user_id TEXT,
            amount REAL,
            type TEXT,
            status TEXT,
            description TEXT,
            created_at TEXT
        )
    ''',
    'team_members': '''
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            parent_id TEXT,
            username TEXT,
            level INTEGER,
            total_contribution REAL,
            created_at TEXT
        )
    ''',
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_id TEXT,
            role TEXT,
            license_type TEXT,
            vip_type TEXT,
            device_quota INTEGER,
            device_limit INTEGER,
            phone TEXT,
            email TEXT,
            activation_code TEXT,
            machine_code TEXT,
            bind_time TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''',
    'activation_codes': '''
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            type TEXT,
            status TEXT,
            bound_account TEXT,
            bound_machine TEXT,
            note TEXT,
            created_at TEXT,
            used_at TEXT,
            expires_at TEXT
        )
    '''
}

# 创建所有表
for table_name, sql in tables.items():
    conn.execute(sql)
    print(f'Created table: {table_name}')

conn.commit()
conn.close()
print('Database initialization complete!')

```
