#!/bin/bash
# Quick Push Script - Stage all, commit with auto message, and push
# Usage: bash quick-push.sh "commit message"

set -e

MESSAGE="${1:-$(date '+%Y-%m-%d %H:%M')}"

echo "=== Git Quick Push ==="
echo ""

# Check if in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a Git repository!"
    exit 1
fi

# Show status
echo "📊 Changes:"
git status --short
echo ""

# Stage all
echo "📦 Staging all changes..."
git add .
echo ""

# Commit
echo "💾 Committing: $MESSAGE"
git commit -m "$MESSAGE"
echo ""

# Push
echo "📤 Pushing to remote..."
CURRENT_BRANCH=$(git branch --show-current)
git push -u origin "$CURRENT_BRANCH"
echo ""

echo "✅ Done! Pushed to $CURRENT_BRANCH"
