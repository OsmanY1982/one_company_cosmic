# -*- coding: utf-8 -*-
"""
gen_book.py — 扫描 OPCclaw 项目所有 .py 文件，为每个模块生成独立文档到 源码全书/ 目录

用法:
    python3 gen_book.py

产出:
    源码全书/ 目录 — 每个 .py 文件独立为一个 .py.md，含路径、行数、完整源码
    源码全书/README.md — 带目录树的索引文件

与宇宙版 gen_book.py 对齐：输出从单文件改为分文件目录，便于增量更新和按模块定位。
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# 项目根目录（本脚本所在目录）
PROJECT_ROOT = Path(__file__).resolve().parent

# 输出目录
OUT_DIR = PROJECT_ROOT / "源码全书"

# 跳过的目录
SKIP_DIRS = {
    "__pycache__", ".git", ".pytest_cache", ".mypy_cache",
    "node_modules", "venv", "deps", "dist", "build", "源码全书",
}

# 要扫描的子目录
SCAN_DIRS = ["core", "modules", "tools", "config"]


def build_tree(path: Path, prefix: str = "") -> list[str]:
    """构建目录树"""
    lines = []
    try:
        entries = sorted(
            [e for e in path.iterdir()
             if e.name not in SKIP_DIRS and not e.name.startswith(".")],
            key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return lines
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            lines.extend(build_tree(entry, prefix + ("    " if i == len(entries) - 1 else "│   ")))
        elif entry.suffix == ".py":
            lines.append(f"{prefix}{connector}{entry.name}")
    return lines


def collect_files(root_dir: Path, scan_subdirs: list) -> list[Path]:
    """递归收集所有 .py 文件"""
    result = []
    for sub in scan_subdirs:
        sub_path = root_dir / sub
        if not sub_path.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(sub_path):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for fname in sorted(filenames):
                if fname.endswith(".py"):
                    result.append(Path(dirpath) / fname)
    return sorted(result)


def main():
    # 清空并重建输出目录
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    files = collect_files(PROJECT_ROOT, SCAN_DIRS)
    total_lines = 0
    total_size = 0

    # 为每个 .py 生成独立 .py.md
    for f in files:
        rel = f.relative_to(PROJECT_ROOT)
        out_subdir = OUT_DIR / rel.parent
        out_subdir.mkdir(parents=True, exist_ok=True)

        out_file = out_subdir / (rel.name + ".md")
        try:
            raw = f.read_text(encoding="utf-8")
        except Exception:
            raw = "# 无法读取"

        lines_count = raw.count("\n") + (0 if raw.endswith("\n") else 1)
        total_lines += lines_count

        md = [f"# `{rel}`\n"]
        md.append(f"> 路径：`{rel}` | 行数：{lines_count}\n\n")
        md.append("---\n\n")
        md.append(f"```python\n{raw}\n```\n")

        content = "\n".join(md)
        out_file.write_text(content, encoding="utf-8")
        total_size += len(content)

    # 生成 README.md 索引
    tree_lines = build_tree(PROJECT_ROOT)
    readme = ["# OPCclaw 源码全书\n"]
    readme.append(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    readme.append(f"> 共 {len(files)} 个模块，每个 `.py` 文件独立为一个文档\n\n")
    readme.append("---\n\n")
    readme.append("## 目录结构\n\n```\n.\n")
    for line in tree_lines:
        readme.append(line + "\n")
    readme.append("```\n\n")
    readme.append("---\n\n")
    readme.append("## 模块列表\n\n")

    for f in files:
        rel = f.relative_to(PROJECT_ROOT)
        md_rel = Path(str(rel) + ".md")
        readme.append(f"- [`{rel}`](./{md_rel})\n")

    index_path = OUT_DIR / "README.md"
    index_path.write_text("".join(readme), encoding="utf-8")

    total_kb = (total_size + len("".join(readme))) / 1024
    print(f"源码全书已更新 — {OUT_DIR}/ ({len(files)} 个模块文件, {total_kb:.1f} KB)")


if __name__ == "__main__":
    main()
