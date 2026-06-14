# `modules/intelligence/edge_tts_engine.py`

> 路径：`modules/intelligence/edge_tts_engine.py` | 行数：189


---


```python
# -*- coding: utf-8 -*-
"""
TTS 语音合成 — edge-tts（微软免费神经网络语音）
零 API Key，类人自然度，中文优秀
"""

import os
import subprocess
import tempfile
import time
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal


# ═══════════ 中文语音预设 ═══════════

VOICES = [
    ("zh-CN-XiaoxiaoNeural",  "活泼少女"),
    ("zh-CN-XiaoyiNeural",    "温柔女声"),
    ("zh-CN-YunxiNeural",     "阳光男声"),
    ("zh-CN-YunjianNeural",   "成熟男声"),
    ("zh-CN-XiaochenNeural",  "自然女声"),
]


class EdgeTTSThread(QThread):
    """基于 edge-tts 的语音合成"""

    finished = pyqtSignal(str)      # 返回 wav 文件路径
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural",
                 rate: str = "+0%", pitch: str = "+0Hz"):
        super().__init__()
        self.text = text
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self._output_path = ""

    def run(self):
        try:
            self.status_changed.emit("合成语音中...")

            # 写入临时文件
            fd, self._output_path = tempfile.mkstemp(suffix=".wav", prefix="opcclaw_tts_")
            os.close(fd)

            cmd = [
                "edge-tts",
                "--voice", self.voice,
                "--rate", self.rate,
                "--pitch", self.pitch,
                "--text", self.text,
                "--write-media", self._output_path,
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self.error_occurred.emit(f"TTS 失败: {result.stderr}")
                return

            if not os.path.exists(self._output_path) or os.path.getsize(self._output_path) < 100:
                self.error_occurred.emit("TTS 生成文件为空")
                return

            self.finished.emit(self._output_path)

        except subprocess.TimeoutExpired:
            self.error_occurred.emit("TTS 合成超时")
        except FileNotFoundError:
            self.error_occurred.emit("未安装 edge-tts，请执行: pip install edge-tts")
        except Exception as e:
            self.error_occurred.emit(f"TTS 异常: {e}")

    def output_path(self) -> str:
        return self._output_path


# ═══════════ 播放器（使用 sounddevice） ═══════════

class AudioPlayer(QThread):
    """播放音频文件"""

    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, wav_path: str):
        super().__init__()
        self.wav_path = wav_path

    def run(self):
        try:
            # 优先用 macOS 原生 afplay（无依赖）
            import subprocess as sp
            result = sp.run(
                ["afplay", self.wav_path],
                capture_output=True, timeout=120
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.decode())

            # 清理临时文件
            try:
                os.remove(self.wav_path)
            except OSError:
                pass
            self.finished.emit()

        except Exception as e:
            # fallback: sounddevice
            try:
                import sounddevice as sd
                import soundfile as sf
                data, sr = sf.read(self.wav_path)
                sd.play(data, sr)
                sd.wait()
                try:
                    os.remove(self.wav_path)
                except OSError:
                    pass
                self.finished.emit()
            except Exception as e2:
                self.error_occurred.emit(f"播放失败: {e} / {e2}")


# ═══════════ 统一 TTS 接口 ═══════════

class TTSInterface:
    """语音合成统一接口（兼容旧 VoiceInterface.speak 签名）"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural",
                 rate: str = "+0%", pitch: str = "+0Hz"):
        self._voice = voice
        self._rate = rate
        self._pitch = pitch
        self._voice_index = 0
        self._tts_thread: Optional[EdgeTTSThread] = None
        self._player: Optional[AudioPlayer] = None

    def speak(self, text: str, voice: str = None, rate: str = None):
        """合成并播放文本"""
        v = voice or self._voice
        r = rate or self._rate

        self._tts_thread = EdgeTTSThread(text, voice=v, rate=r, pitch=self._pitch)
        self._tts_thread.finished.connect(self._on_synthesis_done)
        self._tts_thread.error_occurred.connect(self._on_synthesis_error)
        self._tts_thread.start()

    def _on_synthesis_done(self, wav_path: str):
        """合成完成 → 播放"""
        self._player = AudioPlayer(wav_path)
        self._player.finished.connect(self._on_playback_done)
        self._player.error_occurred.connect(self._on_synthesis_error)
        self._player.start()

    def _on_playback_done(self):
        """播放完毕"""
        # 可通过 signal 通知外部
        pass

    def _on_synthesis_error(self, error: str):
        """合成/播放出错 → 降级到 macOS say"""
        import subprocess
        try:
            subprocess.run(["say", "-v", "Tingting", self._tts_thread.text],
                         capture_output=True, timeout=30)
        except Exception:
            pass

    def next_voice(self) -> str:
        self._voice_index = (self._voice_index + 1) % len(VOICES)
        self._voice = VOICES[self._voice_index][0]
        return f"{VOICES[self._voice_index][1]} ({self._voice})"

    def current_voice(self) -> str:
        return self._voice

    def current_voice_label(self) -> str:
        for v in VOICES:
            if v[0] == self._voice:
                return f"{v[1]} ({v[0]})"
        return self._voice

```
