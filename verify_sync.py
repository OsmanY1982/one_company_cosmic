import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from core import cloud_sync

# 打印配置项数量
db_paths = getattr(cloud_sync, 'DB_PATHS', {})
col_mapping = getattr(cloud_sync, 'COLUMN_MAPPING', {})
print(f"DB_PATHS: {len(db_paths)}")
print(f"COLUMN_MAPPING: {len(col_mapping)}")

# 列出 DB_PATHS 所有 key
print("DB_PATHS keys:", sorted(db_paths.keys()))
print("COLUMN_MAPPING keys:", sorted(col_mapping.keys()))

# 找出差异
db_only = set(db_paths.keys()) - set(col_mapping.keys())
col_only = set(col_mapping.keys()) - set(db_paths.keys())
if db_only:
    print("DB_PATHS中有但COLUMN_MAPPING中无:", db_only)
else:
    print("DB_PATHS与COLUMN_MAPPING对齐: 无缺失")
if col_only:
    print("COLUMN_MAPPING中有但DB_PATHS中无:", col_only)
else:
    print("COLUMN_MAPPING与DB_PATHS对齐: 无多余")

# 检查 sync_all 源码
import inspect
src = inspect.getsource(cloud_sync.sync_all)
import re
calls = re.findall(r'sync_\w+\(', src)
print(f"sync_all()中注册的sync调用数: {len(calls)}")

# 统计模块中 sync_ 函数数量（排除 sync_all 本身）
sync_funcs = [name for name in dir(cloud_sync) if name.startswith('sync_') and name != 'sync_all' and callable(getattr(cloud_sync, name))]
print(f"cloud_sync 模块中 sync_xxx() 函数数: {len(sync_funcs)}")
print("sync_xxx() 函数列表:", sorted(sync_funcs))
