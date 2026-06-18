# `planet_daemon.py`

> 路径：`planet_daemon.py` | 行数：337


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
悬浮星球守护进程入口 - Planet Daemon
独立守护进程，不依赖 Dashboard 主窗口即可常驻后台运行。
支持语音唤醒（Whisper + STT + TTS）+ AI 对话（AgentBridge + opcclaw）。

启动方式：
    python3 planet_daemon.py
    或双击 "启动星球守护.command"
"""

import sys
import os
import json
import atexit
import traceback
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PlanetDaemon] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PlanetDaemon")

# ──────────────────────────────────────────────
# 1. 路径配置
# ──────────────────────────────────────────────
PROJECT_ROOT = "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic"
DATA_DIR = os.path.join(PROJECT_ROOT, "opcclaw", "data")
CONFIG_PATH = os.path.join(DATA_DIR, "opcclaw_config.json")
OPCCLAW_ROOT = PROJECT_ROOT  # opcclaw 与项目同目录

logger.info("PROJECT_ROOT: %s", PROJECT_ROOT)
logger.info("DATA_DIR: %s", DATA_DIR)
logger.info("CONFIG_PATH: %s", CONFIG_PATH)

# 将项目根目录加入 sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    logger.info("已将 PROJECT_ROOT 加入 sys.path")
if OPCCLAW_ROOT not in sys.path:
    sys.path.insert(0, OPCCLAW_ROOT)
    logger.info("已将 OPCCLAW_ROOT 加入 sys.path")


# ──────────────────────────────────────────────
# 2. 加载 opcclaw_config.json
# ──────────────────────────────────────────────
def load_config(config_path: str) -> dict:
    """加载 opcclaw 配置文件。"""
    if not os.path.exists(config_path):
        logger.error("配置文件不存在: %s", config_path)
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info("成功加载配置文件: %s", config_path)
        logger.info(
            "活跃 provider: id=%s, type=%s",
            config.get("active_provider_id"),
            config.get("active_provider_type"),
        )
        return config
    except Exception as e:
        logger.error("加载配置文件失败: %s", e)
        traceback.print_exc()
        return {}


config = load_config(CONFIG_PATH)


# ──────────────────────────────────────────────
# 3. 初始化 opcclaw Engine
# ──────────────────────────────────────────────
def init_opcclaw_engine(config: dict):
    """
    参照 model_setup_window.py 的 _init_opcclaw_engine 方法初始化 engine。
    使用 BackendFactory + AgentBridge 构建。
    失败时优雅降级，返回 None（离线模式）。
    """
    if not config:
        logger.warning("配置为空，跳过 Engine 初始化，将以离线模式运行")
        return None

    try:
        # 3.1 构建 ProviderConfig
        # opcclaw 导入后会把自身路径推到 sys.path[0]，覆盖 PROJECT_ROOT
        # 导致 opcclaw/modules/ 遮蔽项目根 modules/，因此需要重新置顶 PROJECT_ROOT
        from opcclaw.core.llm_backend import BackendFactory, ProviderConfig
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        elif sys.path[0] != PROJECT_ROOT:
            sys.path.remove(PROJECT_ROOT)
            sys.path.insert(0, PROJECT_ROOT)

        active_provider_id = config.get("active_provider_id", "")
        provider_type = config.get("active_provider_type", "local")

        if provider_type == "local":
            provider_data = (
                config.get("local_providers", {}).get(active_provider_id, {})
            )
        else:
            provider_data = (
                config.get("cloud_providers", {}).get(active_provider_id, {})
            )

        if not provider_data:
            logger.error(
                "未找到活跃 provider 配置: id=%s, type=%s",
                active_provider_id,
                provider_type,
            )
            return None

        provider_config = ProviderConfig(
            name=provider_data.get("name", active_provider_id),
            provider_type=provider_data.get("provider_type", "openai_compatible"),
            base_url=provider_data.get("base_url", ""),
            model=provider_data.get("model", ""),
            api_key=provider_data.get("api_key", ""),
        )

        logger.info(
            "ProviderConfig 构建完成: name=%s, model=%s, base_url=%s",
            provider_config.name,
            provider_config.model,
            provider_config.base_url,
        )

        # 3.2 创建 Backend
        backend = BackendFactory.create(provider_config)
        logger.info("LLM Backend 创建成功: %s", type(backend).__name__)

        # 3.3 创建 AgentBridge
        from modules.intelligence.agent_bridge import AgentBridge

        engine = AgentBridge(backend)
        logger.info("AgentBridge (opcclaw Engine) 初始化成功")

        # ── 恢复上次会话 ──
        try:
            msgs = engine.load_session()
            if msgs:
                logger.info("已从磁盘恢复 %d 条对话历史", len(msgs))
        except Exception as e:
            logger.warning("恢复会话历史失败: %s", e)

        return engine

    except Exception as e:
        logger.error("opcclaw Engine 初始化失败: %s", e)
        traceback.print_exc()
        logger.warning("将以离线模式运行（无 AI 对话能力）")
        return None


logger.info("正在初始化 opcclaw Engine...")
engine = init_opcclaw_engine(config)

# ──────────────────────────────────────────────
# 4. 创建 QApplication 并启动悬浮星球
# ──────────────────────────────────────────────
LOCK_FILE = "/tmp/opcclaw_floating_planet.pid"


def _acquire_lock() -> bool:
    """单实例锁：返回 True 表示成功获取锁。"""
    import atexit
    my_pid = os.getpid()
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)  # 检查进程是否存在
            logger.warning("检测到已有实例运行 (PID=%s)，当前进程 (PID=%s) 退出", old_pid, my_pid)
            return False
        except (OSError, ValueError):
            logger.info("旧的锁文件 PID 无效，清理并重新获取")
            os.remove(LOCK_FILE)
    with open(LOCK_FILE, "w") as f:
        f.write(str(my_pid))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))
    logger.info("单实例锁已获取 (PID=%s)", my_pid)
    return True


def main():
    if not _acquire_lock():
        return 0
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPainterPath
        from PyQt5.QtCore import Qt

        logger.info("正在创建 QApplication 实例...")
        app = QApplication(sys.argv)
        app.setApplicationName("FloatingPlanet Daemon")
        # 任务栏图标：一人公司 logo，带圆角裁剪
        _logo_path = os.path.join(PROJECT_ROOT, "logo.jpg")
        if os.path.isfile(_logo_path):
            _src = QPixmap(_logo_path)
            if not _src.isNull():
                _sz = 128
                _src = _src.scaled(_sz, _sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                _rounded = QPixmap(_sz, _sz)
                _rounded.fill(Qt.transparent)
                _p = QPainter(_rounded)
                _p.setRenderHint(QPainter.Antialiasing)
                _path = QPainterPath()
                _r = int(_sz * 0.2237)  # macOS 标准圆角比例
                _path.addRoundedRect(0, 0, _sz, _sz, _r, _r)
                _p.setClipPath(_path)
                _p.drawPixmap(0, 0, _src)
                _p.end()
                app.setWindowIcon(QIcon(_rounded))
                logger.info("任务栏图标已设置（圆角）")
            else:
                logger.warning("logo.jpg 加载失败，使用默认图标")
        else:
            logger.warning("logo.jpg 未找到: %s", _logo_path)
        app.setQuitOnLastWindowClosed(False)  # 守护进程：关闭窗口不退出

        # Cmd+Q 彻底退出：删除 plist + bootout，双保险防止 KeepAlive 重启
        LABEL = "com.opcclaw.planet-daemon"
        PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{LABEL}.plist")
        UID = os.getuid()

        def _daemon_cleanup():
            """纯清理逻辑：删 plist + bootout。由 atexit 和 _graceful_quit 共用。"""
            import subprocess as cleanup_sp
            try:
                os.remove(PLIST_PATH)
                logger.info("已删除 plist: %s", PLIST_PATH)
            except FileNotFoundError:
                pass
            except OSError as e:
                logger.warning("删除 plist 失败: %s", e)
            p = cleanup_sp.run(
                ["launchctl", "bootout", f"gui/{UID}/{LABEL}"],
                capture_output=True, timeout=10,
            )
            if p.returncode != 0:
                logger.info("bootout 返回 %d (已由 plist 删除兜底)", p.returncode)
            else:
                logger.info("bootout 成功")

        # atexit 兜底：无论进程以何种方式退出（Cmd+Q/SIGTERM/normal），都执行清理
        atexit.register(_daemon_cleanup)

        def _graceful_quit():
            logger.info("彻底退出触发，正在清理...")
            _daemon_cleanup()
            app.quit()

        # 导入 FloatingPlanet
        from modules.intelligence.opcclaw_floating_planet import FloatingPlanet

        logger.info("正在创建 FloatingPlanet 实例...")

        if engine is None:
            logger.warning("Engine 为空，FloatingPlanet 将以离线模式运行")
        else:
            logger.info("Engine 已就绪，FloatingPlanet 将具备 AI 对话能力")

        planet = FloatingPlanet(
            opcclaw_engine=engine,
            role="admin",
            membership_info={},
            config=config,
        )

        # 注入守护进程清理回调：右击退出 / closeEvent 均可彻底退出
        planet._daemon_cleanup = _graceful_quit

        planet.show()
        logger.info("悬浮星球已显示")

        # 用 QShortcut + ApplicationShortcut 上下文拦截 Cmd+Q
        # frameless 窗口无键盘焦点，普通 shortcut 不触发
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtCore import Qt
        _quit_shortcut = QShortcut(QKeySequence.Quit, planet)
        _quit_shortcut.setContext(Qt.ApplicationShortcut)
        _quit_shortcut.activated.connect(_graceful_quit)

        # ── 请求麦克风权限 ──
        # LaunchAgent 后台进程无法触发系统权限弹窗，需主动调用 request_mic
        import subprocess as sp
        from PyQt5.QtCore import QTimer

        def _request_mic_permission():
            mic_bin = os.path.join(PROJECT_ROOT, "request_mic")
            if os.path.exists(mic_bin):
                logger.info("正在请求麦克风权限...")
                try:
                    result = sp.run([mic_bin], capture_output=True, text=True, timeout=30)
                    logger.info("request_mic 返回: %s", result.stdout.strip())
                    if result.stderr.strip():
                        logger.warning("request_mic stderr: %s", result.stderr.strip())
                except Exception as e:
                    logger.warning("request_mic 调用失败: %s", e)
            else:
                logger.warning("request_mic 二进制未找到: %s", mic_bin)

        QTimer.singleShot(1500, _request_mic_permission)
        logger.info("进入事件循环（麦克风权限请求将在 1.5s 后触发）")

        exit_code = app.exec()
        logger.info("事件循环结束，exit_code=%s", exit_code)
        return exit_code

    except Exception as e:
        logger.error("守护进程主循环异常退出: %s", e)
        traceback.print_exc()
        return 1


# ──────────────────────────────────────────────
# 5. 入口
# ──────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("悬浮星球守护进程启动中...")
    logger.info("=" * 60)

    exit_code = main()

    logger.info("=" * 60)
    logger.info("悬浮星球守护进程已退出 (exit_code=%s)", exit_code)
    logger.info("=" * 60)

    sys.exit(exit_code)

```
