#!/bin/bash
cd "$(dirname "$0")"
echo "=== 一人公司 - 一键提交代码 ==="
echo ""

REPO_BASE="/Volumes/D盘工作区/一人公司"
REPOS=("one_company_desktop:master" "one_company_mobile:master" "one_company_cosmic:main")

for entry in "${REPOS[@]}"; do
    repo="${entry%%:*}"
    branch="${entry##*:}"
    path="$REPO_BASE/$repo"
    
    if [ ! -d "$path/.git" ]; then
        echo "[跳过] $repo 不存在"
        continue
    fi
    
    echo "[$repo] 检查变更..."
    cd "$path" || continue
    
    if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
        echo "[$repo] 无变更，跳过"
        continue
    fi
    
    git add -A
    git commit -m "自动提交 $(date '+%m-%d %H:%M')" 2>/dev/null || true
    git push origin "$branch" 2>&1
    echo "[$repo] 完成"
done

echo ""
echo "全部完成"
read -p "按回车关闭..."
