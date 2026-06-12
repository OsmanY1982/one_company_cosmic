---
name: macos-system
description: |
  Complete macOS 26 system operations — shell commands, AppleScript automation,
  file management, application control, window operations, clipboard, screenshots,
  system settings, process management, disk & network info, and TCC permission model.
  Load this skill when the user asks for any macOS system-level operation.
  Triggers: macOS系统操作 锁屏 截图 剪贴板 窗口 音量 亮度 关机 重启 文件搜索 进程管理 磁盘 网络 应用启动 系统设置
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [macos, system, shell, applescript, automation, desktop, files, clipboard, screenshot]
    category: system
    related_skills: [macos-computer-use, apple-notes]
tools:
  - execute_shell
  - desktop_control
  - system_control
  - open_application
  - window_control
  - clipboard_read
  - clipboard_write
  - take_screenshot
---

# macOS System Operations

Complete knowledge base for macOS 26 (Apple Silicon) system-level operations.
All commands and patterns are verified on macOS 26 with Apple M5 architecture.

---

## System Architecture

- **OS**: macOS 26 (Darwin kernel)
- **Architecture**: Apple Silicon (ARM64) — `uname -m` returns `arm64`
- **Shell**: zsh (default), Bash available at `/bin/bash`
- **Package Manager**: Homebrew at `/opt/homebrew`

---

## File System Layout

| Path | Purpose |
|---|---|
| `/Users/opc` | User home directory |
| `/Users/opc/Desktop` | Desktop files |
| `/Users/opc/Downloads` | Downloaded files |
| `/Users/opc/Documents` | User documents |
| `/Users/opc/Library` | User library (preferences, caches, app data) |
| `/Applications` | System-wide applications |
| `/System/Applications` | Built-in system applications |
| `/System/Applications/Utilities/Terminal.app` | Terminal |
| `/Volumes` | Mounted volumes & external drives |
| `/opt/homebrew` | Homebrew installation (Apple Silicon) |
| `/tmp` | Temporary files (cleared on reboot) |

### Path Conventions

- Always use POSIX forward slashes: `/Users/opc/Desktop`
- Tilde expansion: `~/Desktop` → `/Users/opc/Desktop`
- Space-escaped paths: `/Users/opc/My\ Files` or quoted `"/Users/opc/My Files"`
- Chinese paths: fully supported, use quotes: `"/Users/opc/桌面/工作报告"`

---

## AppleScript / osascript Patterns

All AppleScript commands use `osascript -e '<script>'`.

### Lock / Sleep / Restart / Shutdown

```bash
# Lock screen
osascript -e 'tell application "System Events" to keystroke "q" using {command down, control down}'

# Sleep
osascript -e 'tell application "System Events" to sleep'

# Restart
osascript -e 'tell application "System Events" to restart'

# Shut down
osascript -e 'tell application "System Events" to shut down'
```

### Volume Control

```bash
# Mute
osascript -e 'set volume with output muted'

# Unmute
osascript -e 'set volume without output muted'

# Set volume to 50%
osascript -e 'set volume output volume 50'

# Increase by 10
osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'

# Decrease by 10
osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'

# Get current volume
osascript -e 'output volume of (get volume settings)'
```

### Brightness Control

```bash
# Set brightness (0.0 - 1.0)
osascript -e 'tell application "System Events" to repeat 32 times
  key code 107
end repeat'  # Brightness up (reduced)

# Alternative: use `brightness` CLI if installed
# brew install brightness
# brightness 0.5
```

### Application Launch & Quit

```bash
# Launch / focus
osascript -e 'tell application "Safari" to activate'

# Quit
osascript -e 'tell application "Safari" to quit'

# Force quit
osascript -e 'tell application "Safari" to quit saving no'

# Launch with open command (simpler)
open -a Safari
open -a "Google Chrome"
open -a 微信
```

### Window Operations

```bash
# Close front window
osascript -e 'tell application "Safari" to close window 1'

# Minimize
osascript -e 'tell application "System Events" to tell process "Safari" to set value of attribute "AXMinimized" of window 1 to true'

# Hide app
osascript -e 'tell application "System Events" to tell process "Safari" to set visible to false'

# Get frontmost app name
osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true'
```

### System Settings Panels

```bash
# Open System Settings
open x-apple.systempreferences:

# Open specific pane (macOS 26)
open "x-apple.systempreferences:com.apple.preference.security"
open "x-apple.systempreferences:com.apple.preference.displays"
open "x-apple.systempreferences:com.apple.preference.sound"
open "x-apple.systempreferences:com.apple.preference.trackpad"
open "x-apple.systempreferences:com.apple.preference.keyboard"
```

### Clipboard

```bash
# Read clipboard
pbpaste

# Write to clipboard
echo "text" | pbcopy

# Copy file content to clipboard
cat /path/to/file | pbcopy

# Clear clipboard
pbcopy < /dev/null
```

### Screenshots

```bash
# Full screen → Desktop
screencapture ~/Desktop/screenshot.png

# Interactive selection
screencapture -i ~/Desktop/selection.png

# Specific window
screencapture -w ~/Desktop/window.png

# Timed (5 second delay)
screencapture -T 5 ~/Desktop/screenshot.png

# To clipboard (no file)
screencapture -c

# Selection to clipboard
screencapture -i -c
```

---

## Shell Command Patterns

### File Search

```bash
# Spotlight search (fast, indexed by macOS)
mdfind "kind:pdf 发票"
mdfind -name "合同" -onlyin ~/Documents
mdfind "kMDItemDisplayName == '*报告*'"

# find command (full scan)
find ~/Desktop -name "*.pdf" -type f
find ~/Documents -mtime -7 -type f  # modified in last 7 days
find ~/Downloads -size +100M  # files > 100MB

# Locate (needs updated db)
locate "*.png" | head -20
```

### File Operations

```bash
# Copy with progress (rsync)
rsync -avh --progress source/ destination/

# Move
mv source target

# Create directory tree
mkdir -p path/to/new/dir

# Create file
touch filename.txt

# Get file size
du -sh /path/to/file
du -sh /path/to/directory

# Count files in directory
ls -1 | wc -l
find . -type f | wc -l
```

### Process Management

```bash
# List processes
ps aux
ps aux | grep Safari

# Find PID
pgrep -f Safari
pgrep -x Terminal

# Kill process
kill <PID>
kill -9 <PID>  # force kill

# Kill all instances
killall Safari
pkill -f "python script.py"

# Check if process is running
pgrep -x Safari > /dev/null && echo "running" || echo "not running"
```

### Disk Information

```bash
# Disk usage overview
df -h

# Directory size
du -sh ~/Desktop

# Largest directories (top 10)
du -sh ~/* | sort -rh | head -10

# Free space on main volume
df -h / | tail -1 | awk '{print $4}'
```

### Network Information

```bash
# Active network interfaces
ifconfig
ifconfig en0  # Wi-Fi

# Current IP address
ipconfig getifaddr en0

# Wi-Fi info
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I

# Network location / proxy
networksetup -listallnetworkservices
networksetup -getdnsservers Wi-Fi

# DNS flush
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### Open / Launch

```bash
# Open file with default app
open file.pdf

# Open directory in Finder
open /Users/opc/Desktop

# Open URL in default browser
open "https://example.com"

# Open with specific app
open -a "Google Chrome" file.html
open -a TextEdit file.txt

# Reveal in Finder
open -R /path/to/file
```

---

## Permission Model (TCC)

macOS uses **TCC (Transparency, Consent, and Control)** for privacy permissions.

### Permission Categories

| Permission | Purpose | Grant via |
|---|---|---|
| Accessibility | Control UI elements, simulate input | System Settings → Privacy → Accessibility |
| Screen Recording | Capture screen content | System Settings → Privacy → Screen Recording |
| Full Disk Access | Access protected directories (~/Desktop, ~/Documents) | System Settings → Privacy → Full Disk Access |
| Automation | Control other apps | Prompted at first use |
| Files and Folders | Access specific directories | Prompted at first use |

### TCC Database

```bash
# Check TCC permissions (requires Full Disk Access)
sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" "SELECT service, client FROM access WHERE auth_value=2"
```

### Security Constraints (NEVER VIOLATE)

- ❌ Never modify `/System`, `/Library` (system), `/bin`, `/sbin`, `/usr`, `/private`
- ❌ Never delete or overwrite `~/.ssh`, `~/.aws`, `~/.kube`, `.env` files
- ❌ Never bypass TCC prompts or modify TCC database directly
- ❌ Never execute destructive commands (`rm -rf /`, `diskutil eraseDisk`) without explicit user confirmation
- ✅ Always move to Trash instead of permanent delete when possible
- ✅ Use `osascript` over direct shell commands for GUI interactions (respects TCC)

---

## Commonly Used Applications

| App | Bundle ID | Launch Command |
|---|---|---|
| Safari | com.apple.Safari | `open -a Safari` |
| Finder | com.apple.finder | Always running |
| Terminal | com.apple.Terminal | `open -a Terminal` |
| System Settings | com.apple.systempreferences | `open x-apple.systempreferences:` |
| Notes | com.apple.Notes | `open -a Notes` |
| Reminders | com.apple.reminders | `open -a Reminders` |
| Mail | com.apple.mail | `open -a Mail` |
| Calendar | com.apple.iCal | `open -a Calendar` |
| Messages | com.apple.iChat | `open -a Messages` |
| Preview | com.apple.Preview | `open -a Preview` |
| TextEdit | com.apple.TextEdit | `open -a TextEdit` |
| Photos | com.apple.Photos | `open -a Photos` |

---

## Quick Reference — When to Use Which Tool

| User Intent | Tool | Example |
|---|---|---|
| Run any shell command | `execute_shell` | `execute_shell("ls -la ~/Desktop")` |
| Open/close/control apps | `open_application` / `desktop_control` | `open_application("Safari")` |
| System settings panel | `system_control` | `system_control("open_system_settings")` |
| Lock/sleep/volume | `system_control` / `desktop_control` | `desktop_control("mute")` |
| Window minimize/close | `window_control` | `window_control("Safari", "minimize")` |
| Read clipboard | `clipboard_read` | `clipboard_read()` |
| Write clipboard | `clipboard_write` | `clipboard_write("hello")` |
| Screenshot | `take_screenshot` | `take_screenshot("selection")` |
