#!/bin/bash
cd "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic"

echo "=== 撤回最近一次提交 ==="

last_commit=$(git log -1 --oneline)
if [ -z "$last_commit" ]; then
    echo "没有可撤回的提交"
    read -p "按回车关闭..."
    exit 1
fi

echo "最近提交: $last_commit"
echo ""
echo "撤回后：代码回到修改前的状态，但改动内容会保留在本地（可继续修改）"
echo ""

read -p "确认撤回？(y/n) " confirm
if [ "$confirm" != "y" ]; then
    echo "已取消"
    exit 0
fi

# 回撤提交但保留改动在本地
git reset --soft HEAD~1

# 远程也撤回
git push origin main --force

echo ""
echo "已撤回。改动内容保留在本地，可继续修改后重新提交。"
read -p "按回车关闭..."
