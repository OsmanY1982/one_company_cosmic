# -*- coding: utf-8 -*-
"""
Voice Manager - 语音管理器
提供语音识别(STT)和语音合成(TTS)功能
"""

import logging
import os
import sys
import tempfile
import threading
import time
from typing import Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


class VoiceWorker(QThread):
    """语音处理工作线程"""
    text_ready = pyqtSignal(str)
    input_error = pyqtSignal(str)
    listening_state = pyqtSignal(bool)
    tts_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_listening = False
        self._is_speaking = False
        self._stop_flag = False

    def run(self):
        """后台线程运行"""
        while not self._stop_flag:
            time.sleep(0.1)

    def stop(self):
        self._stop_flag = True
        self.wait(1000)


class VoiceManager(QObject):
    """语音管理器 - 提供STT和TTS功能"""

    # 信号定义
    text_ready = pyqtSignal(str)           # 语音识别结果
    input_error = pyqtSignal(str)          # 识别错误
    listening_state = pyqtSignal(bool)     # 监听状态变化
    tts_error = pyqtSignal(str)            # TTS错误

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = VoiceWorker()
        self._worker.text_ready.connect(self.text_ready)
        self._worker.input_error.connect(self.input_error)
        self._worker.listening_state.connect(self.listening_state)
        self._worker.tts_error.connect(self.tts_error)
        self._is_listening = False
        self._is_speaking = False
        self._tts_available = False
        self._stt_available = False

        # 检查依赖
        self._check_dependencies()

    def _check_dependencies(self):
        """检查语音依赖是否可用"""
        try:
            # 检查 sounddevice
            import sounddevice as sd
            self._audio_available = True
        except (ImportError, OSError):
            self._audio_available = False
            logger.debug("sounddevice 不可用")

        try:
            # 检查 numpy
            import numpy as np
            self._numpy_available = True
        except ImportError:
            self._numpy_available = False
            logger.debug("numpy 不可用")

        # TTS 可用性检查
        self._tts_available = self._check_tts()
        # STT 可用性检查
        self._stt_available = self._check_stt()

    def _check_tts(self) -> bool:
        """检查TTS是否可用"""
        try:
            # 检查 pyttsx3
            import pyttsx3
            return True
        except ImportError:
            pass

        try:
            # 检查 edge-tts
            import edge_tts
            return True
        except ImportError:
            pass

        # macOS 原生 say 命令
        import shutil
        if shutil.which("say"):
            return True

        return False

    def _check_stt(self) -> bool:
        """检查STT是否可用"""
        try:
            # 检查 whisper
            import whisper
            return True
        except ImportError:
            pass

        try:
            # 检查 speech_recognition
            import speech_recognition as sr
            return True
        except ImportError:
            pass

        return False

    def is_listening(self) -> bool:
        """是否正在监听"""
        return self._is_listening

    def is_speaking(self) -> bool:
        """是否正在播放"""
        return self._is_speaking

    def is_tts_available(self) -> bool:
        """TTS是否可用"""
        return self._tts_available

    def is_stt_available(self) -> bool:
        """STT是否可用"""
        return self._stt_available

    def start_listening(self, timeout: int = 10):
        """开始语音输入监听"""
        if not self._stt_available:
            self.input_error.emit("语音识别依赖未安装")
            return

        if self._is_listening:
            return

        self._is_listening = True
        self.listening_state.emit(True)

        # 在后台线程中执行识别
        threading.Thread(target=self._do_listen, args=(timeout,), daemon=True).start()

    def _do_listen(self, timeout: int):
        """执行语音识别"""
        try:
            # 尝试使用 speech_recognition
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=timeout)
                text = recognizer.recognize_google(audio, language="zh-CN")
                self.text_ready.emit(text)
        except Exception as e:
            self.input_error.emit(f"语音识别失败: {e}")
        finally:
            self._is_listening = False
            self.listening_state.emit(False)

    def stop_listening(self):
        """停止监听"""
        self._is_listening = False
        self.listening_state.emit(False)

    def speak(self, text: str):
        """语音合成播报"""
        if not self._tts_available:
            self.tts_error.emit("语音合成依赖未安装")
            return

        if not text:
            return

        self._is_speaking = True
        threading.Thread(target=self._do_speak, args=(text,), daemon=True).start()

    def _do_speak(self, text: str):
        """执行语音合成"""
        try:
            # 尝试使用 pyttsx3
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return
        except Exception as e1:
            pass

        try:
            # 回退到 edge-tts
            import asyncio
            import edge_tts

            async def _speak():
                communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
                await communicate.save(tempfile.mktemp(suffix=".mp3"))

            asyncio.run(_speak())
            return
        except Exception as e2:
            pass

        try:
            # macOS 原生 say 命令（通过 stdin 传文本避免命令注入）
            import subprocess
            proc = subprocess.Popen(
                ["say"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=text.encode("utf-8"), timeout=60)
        except Exception as e3:
            self.tts_error.emit(f"语音合成失败: {e3}")
        finally:
            self._is_speaking = False

    def stop_speaking(self):
        """停止播报"""
        self._is_speaking = False

    def cleanup(self):
        """清理资源"""
        self.stop_listening()
        self.stop_speaking()
        if self._worker:
            self._worker.stop()


def check_voice_dependencies() -> dict:
    """检查语音依赖状态"""
    deps = {
        "sounddevice": False,
        "numpy": False,
        "pyttsx3": False,
        "edge_tts": False,
        "whisper": False,
        "speech_recognition": False,
    }

    try:
        import sounddevice
        deps["sounddevice"] = True
    except ImportError:
        pass

    try:
        import numpy
        deps["numpy"] = True
    except ImportError:
        pass

    try:
        import pyttsx3
        deps["pyttsx3"] = True
    except ImportError:
        pass

    try:
        import edge_tts
        deps["edge_tts"] = True
    except ImportError:
        pass

    try:
        import whisper
        deps["whisper"] = True
    except ImportError:
        pass

    try:
        import speech_recognition
        deps["speech_recognition"] = True
    except ImportError:
        pass

    return deps
