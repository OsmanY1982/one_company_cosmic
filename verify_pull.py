import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from core import cloud_pull

# 打印配置项数量
table_meta = getattr(cloud_pull, 'TABLE_META', {})
cloud_to_local = getattr(cloud_pull, 'CLOUD_TO_LOCAL', {})
print(f"TABLE_META: {len(table_meta)}")
print(f"CLOUD_TO_LOCAL: {len(cloud_to_local)}")

# 列出 keys
print("TABLE_META keys:", sorted(table_meta.keys()))
print("CLOUD_TO_LOCAL keys:", sorted(cloud_to_local.keys()))

# 找出差异
tm_only = set(table_meta.keys()) - set(cloud_to_local.keys())
cl_only = set(cloud_to_local.keys()) - set(table_meta.keys())
if tm_only:
    print("TABLE_META中有但CLOUD_TO_LOCAL中无:", tm_only)
else:
    print("TABLE_META与CLOUD_TO_LOCAL对齐: 无缺失")
if cl_only:
    print("CLOUD_TO_LOCAL中有但TABLE_META中无:", cl_only)
else:
    print("CLOUD_TO_LOCAL与TABLE_META对齐: 无多余")

# 检查 pull_all_from_cloud 源码
import inspect
src = inspect.getsource(cloud_pull.pull_all_from_cloud)
import re
calls = re.findall(r'pull_\w+\(', src)
print(f"pull_all_from_cloud()中注册的pull调用数: {len(calls)}")

# 统计模块中 pull_ 函数数量（排除 pull_all_from_cloud 本身）
pull_funcs = [name for name in dir(cloud_pull) if name.startswith('pull_') and name != 'pull_all_from_cloud' and callable(getattr(cloud_pull, name))]
print(f"cloud_pull 模块中 pull_xxx() 函数数: {len(pull_funcs)}")
print("pull_xxx() 函数列表:", sorted(pull_funcs))
