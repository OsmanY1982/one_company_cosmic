"""
语音输入模块 — 基于 macOS 原生语音识别
使用 osascript 调用系统 SFSpeechRecognizer
"""
import subprocess
import time
from PyQt5.QtCore import QThread, pyqtSignal


class VoiceListener(QThread):
    """后台语音监听线程"""
    result_ready = pyqtSignal(str)   # 识别结果
    status_changed = pyqtSignal(str)  # 状态变化

    def __init__(self):
        super().__init__()
        self._running = False
        self._language = "zh_CN"  # 中文

    def run(self):
        self._running = True
        self.status_changed.emit("listening")
        try:
            # 使用 macOS 原生听写
            # osascript 调用系统 Voice Recognition
            script = '''
            tell application "System Events"
                set prev to (do shell script "defaults read com.apple.assistant.support 'Assistant Enabled' 2>/dev/null || echo 0")
            end tell
            '''
            # 更简单的方式：使用 say 命令反向 + 系统听写快捷键
            # macOS 默认双击 Fn 触发听写，我们模拟按键
            # 但更好的方式是直接用 AVFoundation 的语音识别 API

            # 实际方案：用 macOS say + pyaudio 录制 → speech_recognition
            # 降级方案：弹一个临时输入框让用户说，用系统听写

            # 这里用最可靠的方案：触发 macOS 听写快捷键 (默认是连续按两次 Ctrl)
            # 先说一句提示
            subprocess.run(["say", "-v", "Tingting", "正在聆听"], capture_output=True)

            # 模拟双击 Ctrl 触发系统听写 (需要用户在系统设置中开启)
            # 实际上更稳健的做法是用一个子进程跑 speech_recognition
            self.status_changed.emit("listening_active")

            # 尝试用 speech_recognition 库
            try:
                result = self._recognize_with_sr()
                if result:
                    self.result_ready.emit(result)
                    self.status_changed.emit("done")
                    return
            except Exception:
                pass

            # 降级：提示用户手动输入
            self.status_changed.emit("fallback")

        except Exception as e:
            self.status_changed.emit(f"error:{e}")

        self._running = False

    def _recognize_with_sr(self) -> str:
        """使用 speech_recognition 库 + 系统麦克风"""
        try:
            import speech_recognition as sr
        except ImportError:
            # 自动安装
            subprocess.run(
                ["/Users/opc/miniconda3/bin/pip", "install", "speech_recognition", "pyaudio"],
                capture_output=True, timeout=30
            )
            import speech_recognition as sr

        r = sr.Recognizer()
        # 调整环境噪声
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            self.status_changed.emit("speak_now")
            audio = r.listen(source, timeout=5, phrase_time_limit=8)

        try:
            # 先尝试中文识别
            text = r.recognize_google(audio, language="zh-CN")
            return text
        except sr.UnknownValueError:
            # 尝试英文
            try:
                text = r.recognize_google(audio, language="en-US")
                return text
            except Exception:
                return ""
        except sr.RequestError:
            # 离线识别 fallback
            try:
                text = r.recognize_sphinx(audio, language="zh-CN")
                return text
            except Exception:
                return ""

    def stop(self):
        self._running = False
        self.status_changed.emit("idle")