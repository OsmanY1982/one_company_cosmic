# Git Commands Reference

## Daily Commands

### Check Status
```bash
git status                    # Full status
git status --short           # Compact status
git diff                     # Show unstaged changes
git diff --staged           # Show staged changes
```

### Basic Operations
```bash
git add <file>              # Stage specific file
git add .                   # Stage all changes
git add -p                  # Stage patches (interactive)
git commit -m "message"     # Commit with message
git commit -am "message"    # Stage tracked AND commit (skip git add)
git push                    # Push to remote
git pull                    # Pull from remote
```

## Branch Management

### List Branches
```bash
git branch                   # Local branches
git branch -r               # Remote branches
git branch -a               # All branches
```

### Create & Switch
```bash
git checkout <branch>       # Switch to branch
git checkout -b <branch>   # Create and switch
git switch <branch>         # Modern switch (Git 2.23+)
git switch -c <branch>      # Create and switch
```

### Delete Branch
```bash
git branch -d <branch>      # Safe delete (merged only)
git branch -D <branch>      # Force delete
git push origin --delete <branch>  # Delete remote branch
```

## Viewing History

### Commit Log
```bash
git log                     # Full log
git log --oneline           # Compact log
git log --graph --oneline   # Visual graph
git log -n 5               # Last 5 commits
git log --author="name"     # Filter by author
git log --since="2 weeks"   # Recent commits
```

### Show Changes
```bash
git show <commit>           # Show commit details
git diff <branch1>..<branch2>  # Diff between branches
git diff HEAD~1            # Diff from last commit
```

## Undo Operations

### Unstage
```bash
git reset HEAD <file>      # Unstage file
git reset HEAD             # Unstage all
```

### Amend
```bash
git commit --amend          # Amend last commit message
git commit --amend --no-edit # Amend without changing message
```

### Revert & Reset
```bash
git revert <commit>         # Create revert commit
git reset --soft HEAD~1    # Undo commit, keep changes staged
git reset --mixed HEAD~1   # Undo commit, keep changes unstaged
git reset --hard HEAD~1    # Undo commit, discard changes (CAREFUL!)
```

## Remote Operations

### Sync with Remote
```bash
git fetch                   # Fetch without merging
git pull                    # Fetch and merge
git pull --rebase          # Fetch and rebase
git push                   # Push
git push -u origin <branch> # Push and set upstream
```

### Work with Remotes
```bash
git remote -v               # Show remotes
git remote add origin <url>  # Add remote
git remote set-url origin <url>  # Change remote URL
```

## Stashing

```bash
git stash                   # Stash changes
git stash pop               # Apply and delete stash
git stash apply            # Apply without deleting
git stash list             # List stashes
git stash drop             # Delete stash
```

## Merge & Rebase

### Merge
```bash
git merge <branch>         # Merge branch into current
git merge --no-ff <branch> # Merge with explicit commit
git merge --abort          # Cancel merge
```

### Rebase
```bash
git rebase <branch>        # Rebase onto branch
git rebase -i HEAD~3       # Interactive rebase last 3 commits
git rebase --continue      # Continue after resolving conflicts
git rebase --abort         # Cancel rebase
```

## Conflict Resolution

```bash
# During merge/rebase conflict
git status                 # Show conflicted files
# Edit conflicted files manually
git add <file>            # Mark as resolved
git commit               # Complete merge/rebase
```

## Configuration

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git config --global core.editor "code --wait"
git config --global pull.rebase false  # Merge strategy
git config --global init.defaultBranch main
```

## Windows Tips

```bash
# Line endings - prevent CRLF issues
git config --global core.autocrlf true

# Use Windows-compatible aliases
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
```

## Common Workflows

### Feature Branch Workflow
```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature
# ... make changes ...
git add .
git commit -m "feat: add my feature"
git push -u origin feature/my-feature
# Create PR on GitHub, then:
git checkout main
git pull origin main
git merge feature/my-feature
git push origin main
git branch -d feature/my-feature
```

### Hotfix Workflow
```bash
git checkout main
git pull origin main
git checkout -b hotfix/urgent-fix
# ... make changes ...
git add .
git commit -m "hotfix: fix critical issue"
git push -u origin hotfix/urgent-fix
# After hotfix is reviewed:
git checkout main
git merge hotfix/urgent-fix
git push origin main
git branch -d hotfix/urgent-fix
```
