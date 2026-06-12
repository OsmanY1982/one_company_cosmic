# -*- coding: utf-8 -*-
"""
语音交互模块 — 多引擎支持
  STT: Apple Speech (macOS 原生) / faster-whisper large-v3 (最强准确率)
  TTS: macOS say / edge-tts (微软 AI 神经网络语音)
"""

import subprocess
import time
import os
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QDialog


# ═══════════ 语音识别: Apple Speech Framework ═══════════

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
            print("[AppleSpeech] 线程启动，开始检查权限...", flush=True)
            from Speech import (
                SFSpeechRecognizer, SFSpeechAudioBufferRecognitionRequest,
                SFSpeechRecognizerAuthorizationStatus,
            )
            import AVFoundation

            status = SFSpeechRecognizer.authorizationStatus()
            expected = SFSpeechRecognizerAuthorizationStatus.Authorized.value

            if status != expected:
                if status == getattr(SFSpeechRecognizerAuthorizationStatus, 'NotDetermined', 0):
                    self.status_changed.emit("正在请求语音权限...")
                    import threading
                    auth_event = threading.Event()
                    auth_result = [None]

                    def auth_handler(new_status, _error):
                        auth_result[0] = new_status
                        auth_event.set()

                    SFSpeechRecognizer.requestAuthorization_(auth_handler)
                    if not auth_event.wait(60.0):
                        self.error_occurred.emit("语音授权超时，请在系统设置中开启")
                        return
                    if auth_result[0] != expected:
                        self.error_occurred.emit("语音识别权限未授权，请在系统设置中开启")
                        return
                else:
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


# ═══════════ 语音合成: macOS say 命令 ═══════════

class AppleSpeechSynthesizer(QThread):
    """基于 macOS say 命令的语音合成线程"""
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, voice: str = "Flo", rate: int = 180):
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


# ═══════════ 语音交互统一接口 ═══════════

class VoiceInterface(QObject):
    """语音交互统一接口 — 支持 Apple / Whisper STT + say / edge-tts TTS"""

    recognition_result = pyqtSignal(str)
    recognition_status = pyqtSignal(str)
    synthesis_done = pyqtSignal()
    error_occurred = pyqtSignal(str)

    # Apple TTS 预设
    CHINESE_VOICES = [
        ("Flo",     180),
        ("Meijia",  175),
        ("Eddy",    180),
        ("Reed",    185),
    ]

    # edge-tts 预设
    EDGE_VOICES = [
        ("zh-CN-XiaoxiaoNeural",  "活泼少女"),
        ("zh-CN-XiaoyiNeural",    "温柔女声"),
        ("zh-CN-YunxiNeural",     "阳光男声"),
        ("zh-CN-YunjianNeural",   "成熟男声"),
        ("zh-CN-XiaochenNeural",  "自然女声"),
    ]

    def __init__(self, stt_engine: str = "auto", tts_engine: str = "auto"):
        """
        Args:
            stt_engine: "apple" / "whisper" / "auto"(优先 Whisper → 降级 Apple)
            tts_engine: "say" / "edge" / "auto"(优先 edge-tts → 降级 say)
        """
        super().__init__()
        self._stt_engine = stt_engine
        self._tts_engine = tts_engine
        print(f"[VoiceInterface] init: stt={stt_engine}, tts={tts_engine}")

        # ── 预检 AVFoundation 可用性（macOS 26 PyObjC 编译兼容性）──
        # 如果 AVFoundation 不可用，只影响 Apple 原生语音识别（SFSpeechRecognizer），
        # Whisper 唤醒 + Edge TTS 仍可正常工作。
        try:
            import AVFoundation  # noqa: F401
            _avfoundation_ok = True
        except ImportError:
            _avfoundation_ok = False
            print("[VoiceInterface] AVFoundation 不可用 (macOS 26 兼容性)，Apple 语音识别不可用；Whisper 唤醒/TTS 正常", flush=True)
            # 不强制禁用 STT — 让用户仍可用 Whisper 唤醒词

        print(f"[VoiceInterface] detected stt={self.stt_engine}, tts={self.tts_engine}")
        self._recognizer: Optional[QThread] = None
        self._synthesizer: Optional[QThread] = None
        self._is_listening = False
        self._voice_index = 0  # Apple voice index
        self._edge_voice_index = 0  # edge-tts voice index

        # 延迟导入的模块引用
        self._whisper_recognizer_cls = None
        self._edge_tts_cls = None

        # ── 在主线程提前请求 Speech Recognition 权限 ──
        # macOS 要求权限弹窗必须在主线程触发，后台线程调用会被静默忽略
        # 仅在 STT 未被禁用时请求权限
        if self.stt_engine != "none":
            self._request_speech_recognition_permission()

    # ── 主线程权限请求 ──

    def _request_speech_recognition_permission(self):
        """在主线程请求麦克风和 Speech Recognition 权限（必须在主线程调用才能弹出系统授权弹窗）"""
        try:
            # ── 1. 先请求麦克风权限 ──
            # 用原生 request_mic 二进制（PyObjC AVFoundation 在 macOS 26 编译失败）
            import subprocess, os
            request_mic_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                "Contents", "MacOS", "request_mic"
            )
            if os.path.exists(request_mic_path):
                print("[VoiceInterface] 调用原生 request_mic 请求麦克风权限...", flush=True)
                result = subprocess.run([request_mic_path], capture_output=True, text=True, timeout=30)
                print(f"[VoiceInterface] request_mic stdout: {result.stdout.strip()}", flush=True)
                if result.stderr.strip():
                    print(f"[VoiceInterface] request_mic stderr: {result.stderr.strip()}", flush=True)
            else:
                print(f"[VoiceInterface] request_mic 未找到: {request_mic_path}", flush=True)

            # ── 2. 再请求 Speech Recognition 权限 ──
            from Speech import SFSpeechRecognizer, SFSpeechRecognizerAuthorizationStatus

            sr_status = SFSpeechRecognizer.authorizationStatus()
            SRAuthorized = SFSpeechRecognizerAuthorizationStatus.Authorized.value
            SRNotDetermined = getattr(SFSpeechRecognizerAuthorizationStatus, 'NotDetermined', 0)

            if sr_status == SRAuthorized:
                print("[VoiceInterface] Speech Recognition 已授权", flush=True)
            elif sr_status == SRNotDetermined:
                print("[VoiceInterface] Speech Recognition NotDetermined，在主线程请求授权...", flush=True)
                SFSpeechRecognizer.requestAuthorization_()
                new_status = SFSpeechRecognizer.authorizationStatus()
                if new_status == SRAuthorized:
                    print("[VoiceInterface] Speech Recognition 授权成功", flush=True)
                else:
                    print(f"[VoiceInterface] Speech Recognition 授权结果: {SFSpeechRecognizerAuthorizationStatus(new_status)}", flush=True)
            else:
                print(f"[VoiceInterface] Speech Recognition 状态: {SFSpeechRecognizerAuthorizationStatus(sr_status)}", flush=True)
        except Exception as e:
            print(f"[VoiceInterface] 权限请求异常: {e}", flush=True)

    # ── 引擎检测 ──

    @property
    def stt_engine(self) -> str:
        """实际使用的 STT 引擎名"""
        if self._stt_engine == "auto":
            return self._detect_stt()
        return self._stt_engine

    @property
    def tts_engine(self) -> str:
        """实际使用的 TTS 引擎名"""
        if self._tts_engine == "auto":
            return self._detect_tts()
        return self._tts_engine

    def _detect_stt(self) -> str:
        try:
            from modules.intelligence.whisper_recognizer import WhisperRecognizer
            self._whisper_recognizer_cls = WhisperRecognizer
            return "whisper"
        except ImportError:
            return "apple"

    def _detect_tts(self) -> str:
        try:
            from modules.intelligence.edge_tts_engine import TTSInterface
            self._edge_tts_cls = TTSInterface
            # 检查 edge-tts 命令是否可用
            import shutil
            if shutil.which("edge-tts"):
                return "edge"
        except ImportError:
            pass
        return "say"

    # ── 识别 ──

    def start_apple_listening(self, timeout: float = 8.0, locale: str = "zh_CN"):
        """强制使用 Apple Speech 识别（不创建 Whisper 实例）"""
        if self._is_listening:
            return
        if self.stt_engine == "none":
            return

        self._is_listening = True
        self._recognizer = AppleSpeechRecognizer(locale=locale, timeout=timeout)
        self._recognizer.status_changed.connect(self.recognition_status.emit)
        self._recognizer.text_ready.connect(self.recognition_result.emit)
        self._recognizer.error_occurred.connect(self._on_recognition_error)
        self._recognizer.finished.connect(self._on_recognition_finished)
        self._recognizer.start()

    def start_listening(self, timeout: float = 8.0, locale: str = "zh_CN"):
        if self._is_listening:
            return
        if self.stt_engine == "none":
            self.error_occurred.emit("语音识别已禁用 (AVFoundation 不可用)")
            return

        self._is_listening = True
        engine = self.stt_engine

        if engine == "whisper":
            if self._whisper_recognizer_cls is None:
                from modules.intelligence.whisper_recognizer import WhisperRecognizer
                self._whisper_recognizer_cls = WhisperRecognizer

            self._recognizer = self._whisper_recognizer_cls(model_size="large-v3")
            self._recognizer.status_changed.connect(self.recognition_status.emit)
            self._recognizer.text_ready.connect(self.recognition_result.emit)
            self._recognizer.error_occurred.connect(self._on_recognition_error)
            self._recognizer.finished.connect(self._on_recognition_finished)
            self._recognizer.set_wake_mode(False)
            self._recognizer.start()

        else:
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
        engine = self.tts_engine

        if engine == "edge":
            if self._edge_tts_cls is None:
                from modules.intelligence.edge_tts_engine import TTSInterface
                self._edge_tts_cls = TTSInterface

            v = voice or self.EDGE_VOICES[self._edge_voice_index][0]
            self._synthesizer = self._edge_tts_cls(
                voice=v,
                rate="+0%",
                pitch="+0Hz",
            )
            # 桥接信号
            self._synthesizer.speak(text)  # 内部已 connect

        else:
            v = voice or self.CHINESE_VOICES[self._voice_index][0]
            r = self.CHINESE_VOICES[self._voice_index][1]
            self._synthesizer = AppleSpeechSynthesizer(text, voice=v, rate=r)
            self._synthesizer.finished.connect(lambda: self.synthesis_done.emit())
            self._synthesizer.error_occurred.connect(lambda e: self.error_occurred.emit(e))
            self._synthesizer.start()

    # ── 切换语音 ──

    def next_voice(self) -> str:
        if self.tts_engine == "edge":
            self._edge_voice_index = (self._edge_voice_index + 1) % len(self.EDGE_VOICES)
            return self.EDGE_VOICES[self._edge_voice_index][1]
        else:
            self._voice_index = (self._voice_index + 1) % len(self.CHINESE_VOICES)
            return self.CHINESE_VOICES[self._voice_index][0]

    def current_voice(self) -> str:
        if self.tts_engine == "edge":
            return self.EDGE_VOICES[self._edge_voice_index][0]
        return self.CHINESE_VOICES[self._voice_index][0]

    def current_voice_label(self) -> str:
        if self.tts_engine == "edge":
            return f"{self.EDGE_VOICES[self._edge_voice_index][1]} ({self.EDGE_VOICES[self._edge_voice_index][0]})"
        return f"{self.CHINESE_VOICES[self._voice_index][0]} ({self.CHINESE_VOICES[self._voice_index][1]}wpm)"


# ═══════════ 语音接口面板 ═══════════

class VoiceWidget(QDialog):
    """语音状态与快捷控制面板"""

    def __init__(self, parent=None):
        from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QPushButton,
                                      QGroupBox, QHBoxLayout, QFrame)
        super().__init__(parent)
        self.setWindowTitle("语音接口")
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #3a3a3a; border-radius: 6px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLabel { color: #ccc; }
            QPushButton { background: #2a2a2a; border: 1px solid #555; border-radius: 4px; padding: 6px 14px; color: #ddd; }
            QPushButton:hover { background: #3a3a3a; border-color: #888; }
            QPushButton:disabled { color: #666; }
        """)

        layout = QVBoxLayout(self)

        # ── 状态区 ──
        status_group = QGroupBox("引擎状态")
        status_layout = QVBoxLayout(status_group)

        self._stt_label = QLabel("语音识别: 检测中...")
        self._tts_label = QLabel("语音合成: 检测中...")
        self._mic_label = QLabel("麦克风: 检测中...")

        status_layout.addWidget(self._stt_label)
        status_layout.addWidget(self._tts_label)
        status_layout.addWidget(self._mic_label)
        layout.addWidget(status_group)

        # ── 快捷操作 ──
        action_group = QGroupBox("快捷操作")
        action_layout = QHBoxLayout(action_group)

        self._mic_btn = QPushButton("测试麦克风")
        self._mic_btn.clicked.connect(self._request_mic)
        action_layout.addWidget(self._mic_btn)

        layout.addWidget(action_group)

        # ── 分隔线 ──
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #3a3a3a;")
        layout.addWidget(line)

        # ── 提示 ──
        hint = QLabel("唤醒词：球球 / 星仔 / 小助手\n登录后悬浮星球自动监听")
        hint.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(hint)

        layout.addStretch()

        self._refresh_status()

    def _test_mic_sync(self) -> tuple:
        """同步测试麦克风：尝试录音 0.5 秒，返回 (ok, message)"""
        try:
            import sounddevice as sd
            import numpy as np

            # 检查输入设备
            devices = sd.query_devices()
            input_devices = [(i, d) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            if not input_devices:
                return False, "未检测到麦克风设备"

            # 尝试录音 0.5 秒（16kHz 单声道）
            recording = sd.rec(
                int(0.5 * 16000), samplerate=16000, channels=1,
                dtype='float32', blocking=True
            )
            sd.wait()

            # 检查是否录到了声音
            if recording is None or recording.size == 0:
                return False, "录音数据为空"
            max_amp = float(np.max(np.abs(recording)))
            if max_amp < 0.001:
                return True, "已授权（未检测到输入音量）"
            return True, "已授权 ✓"
        except Exception as e:
            msg = str(e)
            if "permission" in msg.lower() or "not authorized" in msg.lower() or "-66748" in msg:
                return False, "未授权（需要系统麦克风权限）"
            if "No module" in msg:
                return False, "sounddevice 未安装"
            return False, f"检测失败: {msg[:60]}"

    def _refresh_status(self):
        """刷新引擎和权限状态"""
        from PyQt5.QtCore import QTimer

        # STT
        try:
            from faster_whisper import WhisperModel
            self._stt_label.setText("语音识别: faster-whisper ✓")
            self._stt_label.setStyleSheet("color: #6f6;")
        except Exception:
            self._stt_label.setText("语音识别: faster-whisper 未安装")
            self._stt_label.setStyleSheet("color: #f66;")

        # TTS
        try:
            import edge_tts
            self._tts_label.setText("语音合成: edge-tts ✓")
            self._tts_label.setStyleSheet("color: #6f6;")
        except Exception:
            self._tts_label.setText("语音合成: edge-tts 未安装")
            self._tts_label.setStyleSheet("color: #f66;")

        # 麦克风（异步测试，避免阻塞 UI）
        self._mic_label.setText("麦克风: 检测中...")
        self._mic_label.setStyleSheet("color: #888;")
        self._mic_btn.setEnabled(False)
        QTimer.singleShot(200, self._do_mic_test)

    def _do_mic_test(self):
        ok, msg = self._test_mic_sync()
        if ok:
            self._mic_label.setText(f"麦克风: {msg}")
            self._mic_label.setStyleSheet("color: #6f6;")
            self._mic_btn.setText("麦克风正常")
            self._mic_btn.setEnabled(False)
        elif "未授权" in msg:
            self._mic_label.setText(f"麦克风: {msg}")
            self._mic_label.setStyleSheet("color: #f66;")
            self._mic_btn.setText("打开系统设置")
            self._mic_btn.setEnabled(True)
        elif "设备" in msg:
            self._mic_label.setText(f"麦克风: {msg}")
            self._mic_label.setStyleSheet("color: #fa0;")
            self._mic_btn.setText("重新测试")
            self._mic_btn.setEnabled(True)
        else:
            self._mic_label.setText(f"麦克风: {msg}")
            self._mic_label.setStyleSheet("color: #fa0;")
            self._mic_btn.setText("重新测试")
            self._mic_btn.setEnabled(True)

    def _request_mic(self):
        from PyQt5.QtCore import QTimer
        if "系统设置" in self._mic_btn.text():
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"])
            QTimer.singleShot(3000, self._refresh_status)
            return
        # 测试麦克风（会触发权限弹窗）
        self._mic_btn.setEnabled(False)
        self._mic_btn.setText("测试中...")
        QTimer.singleShot(100, self._do_mic_test)


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
