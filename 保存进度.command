#!/bin/bash
cd "/Volumes/D盘工作区/一人公司/one_company_cosmic"

echo "=== 保存进度 ==="

if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "无变更，无需保存"
    read -p "按回车关闭..."
    exit 0
fi

echo "当前变更："
git status -s
echo ""

read -p "输入本次改动说明（回车用时间戳）: " msg
if [ -z "$msg" ]; then
    msg="$(date '+%m-%d %H:%M')"
fi

git add -A
git commit -m "$msg"
git push origin main

echo ""
echo "已保存并推送"
read -p "按回车关闭..."
