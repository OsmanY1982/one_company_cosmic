# `modules/intelligence/voice_interface.py`

> 路径：`modules/intelligence/voice_interface.py` | 行数：251


---


```python
# -*- coding: utf-8 -*-
"""
语音交互模块 — macOS 原生 Apple Speech Framework + say 命令
零第三方依赖（PyObjC 除外），离线可用，中文识别准确率高
"""

import subprocess
import time
import os
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal, QObject


# ═══════════ 语音识别（Apple Speech Framework） ═══════════

class AppleSpeechRecognizer(QThread):
    """基于 Apple Speech Framework 的语音识别线程"""
    text_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, locale: str = "zh_CN", timeout: float = 10.0):
        super().__init__()
        self.locale = locale
        self.timeout = timeout
        self._running = True

    def run(self):
        try:
            from Speech import (
                SFSpeechRecognizer, SFSpeechAudioBufferRecognitionRequest,
                SFSpeechRecognizerAuthorizationStatus,
            )
            import AVFoundation

            # 权限检查
            status = SFSpeechRecognizer.authorizationStatus()
            expected = SFSpeechRecognizerAuthorizationStatus.Authorized.value
            if status != expected:
                self.error_occurred.emit("语音识别权限未授权，请在系统设置中开启")
                return

            ns_locale = __import__('Foundation', fromlist=['NSLocale']).NSLocale
            locale_obj = ns_locale.localeWithLocaleIdentifier_(self.locale)
            recognizer = SFSpeechRecognizer.alloc().initWithLocale_(locale_obj)
            if not recognizer or not recognizer.isAvailable():
                self.error_occurred.emit("当前地区的语音识别不可用")
                return

            audio_engine = AVFoundation.AVAudioEngine.alloc().init()
            input_node = audio_engine.inputNode()
            bus = 0
            native_format = input_node.outputFormatForBus_(bus)

            request = SFSpeechAudioBufferRecognitionRequest.alloc().init()
            request.shouldReportPartialResults = True
            request.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition()

            input_node.installTapOnBus_bufferSize_format_block_(
                bus, 1024, native_format,
                lambda buf, _when: request.appendAudioPCMBuffer_(buf),
            )

            audio_engine.prepare()
            objc_module = __import__('objc', fromlist=['objc'])
            error_ptr = objc_module.objc.nil
            success, _ = audio_engine.startAndReturnError_(error_ptr)
            if not success:
                self.error_occurred.emit("无法启动麦克风")
                return

            self.status_changed.emit("正在聆听...")

            result_container = [""]

            def result_handler(result, error):
                if not self._running:
                    return
                if error:
                    ns_error = error
                    self.error_occurred.emit(f"识别错误: {ns_error}")
                elif result:
                    final_str = result.bestTranscription().formattedString()
                    if result.isFinal():
                        result_container[0] = final_str
                    else:
                        self.text_ready.emit(final_str)

            task = recognizer.recognitionTaskWithRequest_resultHandler_(
                request, result_handler,
            )

            elapsed = 0.0
            while self._running and elapsed < self.timeout:
                time.sleep(0.1)
                elapsed += 0.1
                if task.isFinishing() or task.isCancelled():
                    break

            if self._running:
                task.finish()
            audio_engine.stop()
            input_node.removeTapOnBus_(bus)

            final_text = result_container[0]
            if not final_text.strip() and hasattr(task, 'bestTranscription') and task.bestTranscription():
                final_text = task.bestTranscription().formattedString()

            if final_text.strip():
                self.text_ready.emit(final_text)
            else:
                self.error_occurred.emit("未能识别到语音")

        except ImportError as e:
            self.error_occurred.emit(f"缺少依赖: {e}")
        except Exception as e:
            self.error_occurred.emit(f"语音识别异常: {e}")

    def stop(self):
        self._running = False


# ═══════════ 语音合成（macOS say 命令） ═══════════

class AppleSpeechSynthesizer(QThread):
    """基于 macOS say 命令的语音合成线程"""
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, voice: str = "Flo", rate: int = 180):
        """
        Args:
            text: 要合成的文本
            voice: 语音名（Flo/Meijia/Eddy/Reed）
            rate: 语速（字/分钟），默认 180
        """
        super().__init__()
        self.text = text
        self.voice = voice
        self.rate = rate

    def run(self):
        try:
            cmd = ["say", "-v", self.voice, "-r", str(self.rate), self.text]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.finished.emit()
            else:
                self.error_occurred.emit(f"语音合成失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.error_occurred.emit("语音合成超时")
        except FileNotFoundError:
            self.error_occurred.emit("系统未找到 say 命令")
        except Exception as e:
            self.error_occurred.emit(f"语音合成异常: {e}")


# ═══════════ 语音交互接口 ═══════════

class VoiceInterface(QObject):
    """语音交互统一接口 — 识别 + 合成 + 状态管理"""

    recognition_result = pyqtSignal(str)
    recognition_status = pyqtSignal(str)
    synthesis_done = pyqtSignal()
    error_occurred = pyqtSignal(str)

    CHINESE_VOICES = [
        ("Flo",     180),    # 大陆女声，自然流畅
        ("Meijia",  175),    # 台湾女声，甜美
        ("Eddy",    180),    # 大陆男声
        ("Reed",    185),    # 男声
    ]

    def __init__(self):
        super().__init__()
        self._recognizer: Optional[AppleSpeechRecognizer] = None
        self._synthesizer: Optional[AppleSpeechSynthesizer] = None
        self._is_listening = False
        self._voice_index = 0

    # ── 识别 ──

    def start_listening(self, timeout: float = 8.0, locale: str = "zh_CN"):
        """开始语音识别"""
        if self._is_listening:
            return

        self._is_listening = True
        self._recognizer = AppleSpeechRecognizer(locale=locale, timeout=timeout)
        self._recognizer.status_changed.connect(self.recognition_status.emit)
        self._recognizer.text_ready.connect(self.recognition_result.emit)
        self._recognizer.error_occurred.connect(self._on_recognition_error)
        self._recognizer.finished.connect(self._on_recognition_finished)
        self._recognizer.start()

    def stop_listening(self):
        self._is_listening = False
        if self._recognizer and self._recognizer.isRunning():
            self._recognizer.stop()
            self._recognizer.wait(1500)

    def is_listening(self) -> bool:
        return self._is_listening

    def _on_recognition_error(self, error: str):
        self._is_listening = False
        self.error_occurred.emit(error)

    def _on_recognition_finished(self):
        self._is_listening = False

    # ── 合成 ──

    def speak(self, text: str, voice: str = None):
        """朗读文本（直接播放）"""
        v = voice or self.CHINESE_VOICES[self._voice_index][0]
        r = self.CHINESE_VOICES[self._voice_index][1]
        self._synthesizer = AppleSpeechSynthesizer(text, voice=v, rate=r)
        self._synthesizer.finished.connect(lambda: self.synthesis_done.emit())
        self._synthesizer.error_occurred.connect(lambda e: self.error_occurred.emit(e))
        self._synthesizer.start()

    # ── 切换语音 ──

    def next_voice(self) -> str:
        self._voice_index = (self._voice_index + 1) % len(self.CHINESE_VOICES)
        return self.CHINESE_VOICES[self._voice_index][0]

    def current_voice(self) -> str:
        return self.CHINESE_VOICES[self._voice_index][0]

    def current_voice_label(self) -> str:
        return f"{self.CHINESE_VOICES[self._voice_index][0]} ({self.CHINESE_VOICES[self._voice_index][1]}wpm)"


# ═══════════ 快捷测试 ═══════════

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    vi = VoiceInterface()
    vi.recognition_result.connect(lambda t: print(f"识别: {t}"))
    vi.error_occurred.connect(lambda e: print(f"错误: {e}"))

    print("开始语音识别（8秒）...")
    vi.start_listening(timeout=8.0)
    sys.exit(app.exec_())

```
