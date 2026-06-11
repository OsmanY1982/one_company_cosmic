#!/bin/bash

# 一人公司 · 宇宙版 — 启动脚本

PYTHON="/usr/bin/python3"
PROJECT="/Volumes/D盘工作区/一人公司/one_company_cosmic"

echo "=========================================="
echo "  一人公司 · 宇宙版 COSMIC v2.0"
echo "=========================================="
echo "Python: $PYTHON"
echo "项目:   $PROJECT"
echo "=========================================="

cd "$PROJECT" || { echo "项目路径不存在"; exit 1; }
echo "✅ Python版本: $($PYTHON --version 2>&1)"
echo ""

"$PYTHON" main.py 2>&1
EXIT_CODE=$?

echo ""
echo "退出状态: $EXIT_CODE"
echo "按任意键退出..."
read -n 1
