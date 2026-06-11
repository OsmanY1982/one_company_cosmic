---
name: git-workflow
description: "Git version control workflow automation for Windows. Use when user needs help with: (1) Committing changes with good commit messages, (2) Branch management (create, switch, merge, delete), (3) Push/pull operations, (4) Viewing git history and diffs, (5) Resolving merge conflicts, (6) Git configuration. Triggers: git commit, git push, git branch, 创建分支, 提交代码, 查看提交历史."
---

# Git Workflow

## Overview

Provides comprehensive Git workflow automation and best practices for Windows environments. Helps execute common Git operations efficiently with proper commit message formatting and branch management.

## Quick Reference

### Common Commands

```bash
# Check status
git status

# Stage changes
git add <file>        # Stage specific file
git add .             # Stage all changes

# Commit with message
git commit -m "type: description"

# Push/Pull
git push
git pull

# Branch operations
git branch                    # List branches
git branch -a                 # List all branches (including remote)
git checkout <branch>         # Switch branch
git checkout -b <new-branch>   # Create and switch to new branch
git merge <branch>            # Merge branch
git branch -d <branch>        # Delete branch
```

### Commit Message Format

```
type: short description (max 50 chars)

Optional longer description here if needed.
Wrap at 72 characters.
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `hotfix`

## Branch Naming

```
feature/description      # New features
bugfix/description       # Bug fixes
hotfix/description       # Urgent fixes
refactor/description     # Code refactoring
docs/description         # Documentation
```

## Workflow Examples

### Feature Development Flow

```bash
# 1. Update main branch
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-new-feature

# 3. Make changes and commit
git add .
git commit -m "feat: add new feature"

# 4. Push to remote
git push -u origin feature/my-new-feature

# 5. After review, merge to main
git checkout main
git pull origin main
git merge feature/my-new-feature
git push origin main
```

### Daily Commit Flow

```bash
# Check what changed
git status
git diff

# Stage and commit
git add .
git commit -m "fix: resolve issue with login"

# Push
git push
```

## Windows-Specific Tips

- Use Git Bash or Windows Terminal for best experience
- Paths use forward slashes `/` in Git commands
- Line endings: `git config --global core.autocrlf true` (Windows)

## Scripts

This skill includes automation scripts in `scripts/`:
- `commit.sh` - Interactive commit with type selection and message formatting
- `quick-push.sh` - Stage all, commit with timestamp, and push in one command
- `branch-cleanup.sh` - Delete merged local branches

Run scripts with: `bash <script-path>` or double-click `.bat` versions on Windows.
