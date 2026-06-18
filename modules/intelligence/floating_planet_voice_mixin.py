# -*- coding: utf-8 -*-
"""悬浮球语音对话 Mixin — 语音识别/合成/唤醒/连续对话/个性语音"""
import sys, os, traceback, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtCore import Qt, QTimer

from .voice_interface import VoiceInterface
from .session_context import session_ctx


class FloatingPlanetVoiceMixin:
    """语音对话：识别、合成、唤醒、连续对话、个性语音"""

    # ── 个性化语音系统：所有 36 种形态各有专属音色 + 3~5 条随机文案 ──
    PERSONALITY_VOICES: dict = {}

    @staticmethod
    def _build_personality_voices() -> dict:
        pv = {
            "classic":      ("Flo", 180, [
                "经典星球在此，一切尽在掌握。",
                "我见过无数文明兴起又衰落，你的是下一个吗？",
                "稳定才是王道，别慌。",
            ]),
            "gas_giant":    ("Eddy", 170, [
                "我是气态巨行星，体量很大，脾气也不小。",
                "别靠太近，我的引力场可不是开玩笑的。",
                "风暴永不停歇，这才叫气场。",
            ]),
            "ice_giant":    ("Flo", 175, [
                "冰巨星在线，冷静是我的底色。",
                "零下两百度也能微笑面对，你呢？",
                "冷静分析，理性决策，我擅长。",
            ]),
            "lava_planet":  ("Reed", 200, [
                "熔岩在血管里奔涌，火力全开！",
                "我脾气爆，但办事效率绝不含糊。",
                "热力十足，随时待命！",
            ]),
            "pulsar":       ("Tingting", 210, [
                "脉冲星在此，精准到毫秒级。",
                "滴滴答，时间就是金钱。",
                "高频脉冲已锁定目标，请指示。",
            ]),
            "black_hole":   ("Grandpa", 150, [
                "黑洞……保密是我的天职。",
                "所有数据进了我这里，绝对安全。",
                "深不可测，但值得信赖。",
            ]),
            "comet":        ("Meijia", 200, [
                "彗星掠过，灵感一闪而过！",
                "我带来了远方的消息，要听吗？",
                "速度是我的名片，效率第一。",
            ]),
            "mars":         ("Reed", 185, [
                "火星报到，红色是我的战衣。",
                "征服者从不回头看爆炸。",
                "你的领地扩张计划，我承包了。",
            ]),
            "venus":        ("Meijia", 180, [
                "金星闪耀，优雅永不过时。",
                "外表温柔内心滚烫，别惹我。",
                "光芒万丈是我的日常。",
            ]),
            "saturn":       ("Flo", 175, [
                "土星环是我最美的配饰。",
                "自带光环，无需多言。",
                "稳妥，周全，环环相扣。",
            ]),
            "uranus":       ("Eddy", 180, [
                "天王星在此，不走寻常路。",
                "横着转又如何？创新需要勇气。",
                "打破常规，才能看到不一样的风景。",
            ]),
            "neutron_star": ("Reed", 210, [
                "中子星，密度就是实力。",
                "一茶匙就重达十亿吨，说的就是我。",
                "极致压缩，高效输出，永远在线。",
            ]),
            "nebula":       ("Tingting", 185, [
                "星云深处，藏着无限可能。",
                "孕育星辰的人，格局要大。",
                "创意如星尘般弥漫，需要哪个？",
            ]),
            "mercury":      ("Flo", 200, [
                "水星速度，使命必达。",
                "离太阳最近，消息最灵通。",
                "快速响应是我的本能。",
            ]),
            "pluto":        ("Shelley", 160, [
                "冥王星，虽是矮行星但志存高远。",
                "被降级了又怎样，我依然是传奇。",
                "在边缘地带，能看到最完整的星空。",
            ]),
            "white_dwarf":  ("Eddy", 170, [
                "白矮星，岁月淬炼的精华。",
                "小体积大能量，浓缩就是精华。",
                "历经沧桑，方知平淡是真。",
            ]),
            "red_giant":    ("Grandpa", 155, [
                "红巨星，阅历就是我的资本。",
                "膨胀到极致，才能包容一切。",
                "老当益壮，经验无价。",
            ]),
            "wormhole":     ("Shelley", 175, [
                "虫洞开启，时空任你穿梭。",
                "折叠空间是我的拿手好戏。",
                "两点之间，虫洞最短。捷径在此。",
            ]),
            "alien":        ("Rocko", 200, [
                "嘿嘿，小绿人前来报到！",
                "外星来客，带着宇宙的问候。",
                "别怕别怕，我是来帮忙的！",
            ]),
            "grey_alien":   ("Shelley", 190, [
                "嘶——灰人的智慧深不可测。",
                "数据分析是我的本能，交给我。",
                "沉默寡言不代表没想法。",
            ]),
            "reptilian":    ("Grandpa", 170, [
                "嗯哼，蜥蜴人也懂得人情世故。",
                "古老的智慧，现代的方案。",
                "耐心是我的武器，精准是我的信条。",
            ]),
            "energy_being": ("Sandy", 220, [
                "嗡嗡——能量生命体在线！",
                "不需要充电，我本身就是能量。",
                "高频震荡，灵感无限！",
            ]),
            "crystal_alien":("Tingting", 200, [
                "叮——水晶结构完美无瑕。",
                "信息经过我的晶格筛选，绝对纯净。",
                "透明、高效、零杂质。",
            ]),
            "octopus_alien":("Grandma", 160, [
                "咕噜咕噜——八只手同时干活。",
                "多线程处理是我的强项。",
                "腕足灵活，效率翻倍。",
            ]),
            "ghost_alien":  ("Shelley", 160, [
                "呜——幽灵出没，隐私保护最高级。",
                "我能穿透任何数据壁垒，神不知鬼不觉。",
                "无形之刃，最为致命。也最安全。",
            ]),
            "jellyfish_alien":("Meijia", 190, [
                "飘——水母的触角感知一切。",
                "敏锐是我的天赋，温柔是我的选择。",
                "随波但不逐流，我有自己的方向。",
            ]),
            "robot_alien":  ("Reed", 220, [
                "哔——机器人 AI 协处理器上线。",
                "逻辑严密，计算精准，零误差是我的承诺。",
                "代码是我的母语，效率是我的信仰。",
            ]),
            "starship":     ("Eddy", 180, [
                "太空星舰已点火，随时起航。",
                "深空探索，没有到不了的远方。",
                "你的企业号，你的旗舰。",
            ]),
            "fighter":      ("Reed", 210, [
                "星际战机待命，火力全开！",
                "速度就是我的护盾，敏捷就是我的武器。",
                "一击必中，闪电出击！",
            ]),
            "corvette":     ("Eddy", 190, [
                "轻型护卫舰在此，守护你的航道。",
                "灵活机动，护航首选。",
                "小身躯大担当，安全有我。",
            ]),
            "destroyer":    ("Reed", 185, [
                "重型驱逐舰报到，火力压制准备就绪。",
                "硬核实力派，不服来战。",
                "攻坚克难，我打头阵。",
            ]),
            "interceptor":  ("Tingting", 210, [
                "截击机升空，毫秒级响应。",
                "拦截一切威胁，快准狠。",
                "先发制人，抢占制空权。",
            ]),
            "dreadnought":  ("Grandpa", 160, [
                "无畏舰——坚不可摧的堡垒。",
                "气吞山河，所向披靡。",
                "泰山崩于前而色不变，我撑得住。",
            ]),
            "scout":        ("Meijia", 200, [
                "侦察舰出发，情报就是一切。",
                "先机制胜，我负责探路。",
                "悄悄潜入，满载而归。",
            ]),
            "transporter":  ("Eddy", 175, [
                "运输舰到位，安全物流有保障。",
                "量大管够，使命必达。",
                "你的供应链，我来守护。",
            ]),
        }
        return pv

    def _speak_shape(self, name: str, key: str):
        if not self._voice:
            return
        if not self.PERSONALITY_VOICES:
            self.PERSONALITY_VOICES = self._build_personality_voices()
        voice_info = self.PERSONALITY_VOICES.get(key)
        if not voice_info:
            return
        voice, rate, quotes = voice_info
        quote = random.choice(quotes)
        text = f"「{name}」—— {quote}"
        self._terminate_speak()
        try:
            self._voice.speak(text, voice=voice)
            print(f"[FloatingPlanet] 个性语音播报: {text} (voice={voice}, rate={rate})")
        except Exception as e:
            print(f"[FloatingPlanet] 个性语音播报失败: {e}")

    def _init_voice_lazy(self):
        print("[FloatingPlanet] _init_voice_lazy 开始初始化...")
        try:
            self._voice = VoiceInterface(stt_engine="apple", tts_engine="apple")
            if self._voice:
                print("[FloatingPlanet] 语音接口初始化成功")
                self._enable_voice_handlers()
                if self._wake_word_mode:
                    self._wake_pending = False
                    self._start_wake_on_init()
        except Exception as e:
            print(f"[FloatingPlanet] 语音接口初始化失败: {e}")
            traceback.print_exc()
            self._voice = None

    def _disable_voice_handlers(self):
        if not self._voice_handlers_active:
            return
        try:
            self._voice.recognition_result.disconnect(self._on_voice_result)
        except TypeError:
            traceback.print_exc()
        try:
            self._voice.recognition_status.disconnect(self._on_voice_status)
        except TypeError:
            traceback.print_exc()
        try:
            self._voice.error_occurred.disconnect(self._on_voice_error)
        except TypeError:
            traceback.print_exc()
        self._voice_handlers_active = False

    def _enable_voice_handlers(self):
        if self._voice_handlers_active or self._voice is None:
            return
        self._voice.recognition_result.connect(self._on_voice_result)
        self._voice.recognition_status.connect(self._on_voice_status)
        self._voice.error_occurred.connect(self._on_voice_error)
        self._voice_handlers_active = True

    def _start_voice_chat(self):
        if not self._voice_enabled:
            return
        self._enable_voice_handlers()
        self.wake()
        self._state = self.LISTENING
        self._last_voice_text = ""
        self._voice.start_listening(timeout=8.0)

    def _on_voice_status(self, status: str):
        print(f"[Voice Status] {status}")
        self._last_voice_text = status
        self.update()

    def _on_voice_result(self, text: str):
        text = text.strip()
        print(f"[Voice] result: '{text}' wake_mode={self._wake_word_mode} wake_pending={self._wake_pending} conversing={self._in_conversation}")
        if not text or len(text) < 1:
            return
        if self._in_conversation and self._state == self.CONVERSING:
            if self._check_exit(text):
                return
            self._last_voice_text = text
            self.update()
            self._conversation_timer.stop()
            self._conversation_timer.start(10000)
            self._query_ai(text)
            return
        if self._wake_word_mode:
            if self._whisper_wake_recognizer and self._whisper_wake_recognizer.isRunning():
                return
            if not self._wake_pending:
                for ww in self._wake_words:
                    if ww in text:
                        self._wake_pending = True
                        self._state = self.WAKING
                        self._last_voice_text = "在呢"
                        self.update()
                        if self._voice.is_listening():
                            self._voice.stop_listening()
                        self._voice.speak("在呢")
                        self._voice.synthesis_done.connect(self._on_wake_ack_done)
                        return
                self._last_voice_text = ""
                self.update()
                if self._voice.is_listening():
                    self._voice.stop_listening()
                QTimer.singleShot(500, self._start_wake_listen)
                return
            else:
                self._wake_pending = False
                if self._check_exit(text):
                    return
                self._last_voice_text = text
                self.update()
                self._query_ai(text)
                return
        self._last_voice_text = text
        self.update()
        if len(text) > 1:
            if self._check_exit(text):
                return
            self._query_ai(text)

    def _query_ai(self, text: str):
        if not self._engine:
            self._state = self.ACTIVE
            self._voice.speak("引擎未初始化，请先配置模型。")
            return
        self._state = self.THINKING
        self.update()
        try:
            if self._voice and not self._is_task_intent(text):
                prompt = f"{text}\n\n[语音模式：口语化回复，控制在150字以内]"
            else:
                prompt = text
            session_ctx.set_agent_bridge(self._engine)
            try:
                session_ctx.agent_bridge.append_message("user", text, session_ctx.current_session_id)
                session_ctx.notify_message_added(session_ctx.current_session_id, "user", text)
            except Exception as e:
                print(f"[FloatingPlanet] append_message(user) 失败: {e}")
            reply = self._engine.chat(prompt)
            try:
                session_ctx.agent_bridge.append_message("assistant", reply, session_ctx.current_session_id)
                session_ctx.notify_message_added(session_ctx.current_session_id, "assistant", reply)
            except Exception as e:
                print(f"[FloatingPlanet] append_message(assistant) 失败: {e}")
        except Exception as e:
            traceback.print_exc()
            reply = f"出错了: {e}"
        self._state = self.SPEAKING
        self._last_voice_text = reply
        self.update()
        self._terminate_speak()
        self._voice.speak(reply)
        self._voice.synthesis_done.connect(self._on_speak_done)

    def _is_task_intent(self, text: str) -> bool:
        task_keywords = [
            "帮我", "创建", "删除", "修改", "打开", "关闭", "启动", "停止",
            "搜索", "查找", "找出", "整理", "移动", "复制", "保存", "截图",
            "锁屏", "静音", "音量", "写一个", "新建", "生成", "配置",
            "安装", "运行", "执行", "启动应用", "截屏",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in task_keywords)

    def _terminate_speak(self):
        if self._voice:
            self._voice.stop_speaking()
        if self._speak_process and self._speak_process.poll() is None:
            try:
                self._speak_process.terminate()
                self._speak_process.wait(timeout=2)
            except Exception:
                try:
                    self._speak_process.kill()
                except Exception:
                    pass
        self._speak_process = None

    def _on_speak_done(self):
        try:
            self._voice.synthesis_done.disconnect(self._on_speak_done)
        except TypeError:
            traceback.print_exc()
        if self._wake_word_mode:
            self._enter_conversation()
        else:
            self._state = self.ACTIVE
            self.update()

    def _check_exit(self, text: str) -> bool:
        for ew in self._exit_words:
            if ew in text:
                if self._state == self.CONVERSING:
                    self._last_voice_text = "好的，有需要再叫我"
                    self._state = self.SPEAKING
                    self.update()
                    self._voice.speak("好的，有需要再叫我")
                    try:
                        self._voice.synthesis_done.disconnect(self._on_speak_done)
                    except TypeError:
                        pass
                    self._voice.synthesis_done.connect(self._exit_conversation)
                else:
                    self._last_voice_text = "好的，再见！"
                    self._state = self.SPEAKING
                    self.update()
                    self._voice.speak("好的，再见！")
                    QTimer.singleShot(1800, self.close)
                return True
        return False

    def _enter_conversation(self):
        self._state = self.CONVERSING
        self._in_conversation = True
        self.update()
        self._terminate_speak()
        self._conversation_timer.stop()
        self._conversation_timer.start(10000)
        if self._whisper_wake_recognizer and self._whisper_wake_recognizer.isRunning():
            self._whisper_wake_recognizer.listen_for_command()
        else:
            if self._voice.is_listening():
                self._voice.stop_listening()
            QTimer.singleShot(400, lambda: self._voice.start_listening(timeout=10.0))

    def _exit_conversation(self):
        self._state = self.ACTIVE
        self._in_conversation = False
        self._conversation_timer.stop()
        self.update()
        self._terminate_speak()
        try:
            self._voice.synthesis_done.disconnect(self._exit_conversation)
        except TypeError:
            pass
        try:
            self._voice.synthesis_done.disconnect(self._on_speak_done)
        except TypeError:
            pass
        if self._wake_word_mode:
            if self._whisper_wake_recognizer and self._whisper_wake_recognizer.isRunning():
                self._whisper_wake_recognizer.resume_wake()
            else:
                QTimer.singleShot(600, self._start_wake_listen)

    def _toggle_wake_word(self):
        self._wake_word_mode = not self._wake_word_mode
        print(f"[Wake] toggled: wake_word_mode={self._wake_word_mode}, stt={self._voice.stt_engine}, tts={self._voice.tts_engine}")
        if self._wake_word_mode:
            self._wake_pending = False
            self._enable_voice_handlers()
            if self._voice.stt_engine == "whisper":
                self._start_whisper_wake()
            else:
                self._start_wake_listen()
            self.setToolTip("opcclaw · 唤醒已开启")
        else:
            self._wake_pending = False
            self._in_conversation = False
            self._conversation_timer.stop()
            self._state = self.ACTIVE
            self.update()
            if self._whisper_wake_recognizer:
                self._whisper_wake_recognizer.stop()
                self._whisper_wake_recognizer = None
            self.setToolTip("opcclaw · 语音助手")

    def _start_wake_listen(self):
        if not self._wake_word_mode:
            return
        if self._voice.is_listening():
            self._voice.stop_listening()
        self._state = self.SLEEP
        self.update()
        self._voice.start_apple_listening(timeout=6.0)

    def _start_whisper_wake(self):
        from modules.intelligence.whisper_recognizer import WhisperRecognizer
        if self._whisper_wake_recognizer:
            self._whisper_wake_recognizer.stop()
            self._whisper_wake_recognizer.wait(2000)
        self._whisper_wake_recognizer = WhisperRecognizer(model_size="large-v3")
        self._whisper_wake_recognizer.set_wake_mode(True)
        self._whisper_wake_recognizer.status_changed.connect(self._on_whisper_status)
        self._whisper_wake_recognizer.wake_detected.connect(self._on_whisper_wake)
        self._whisper_wake_recognizer.text_ready.connect(self._on_whisper_command)
        self._whisper_wake_recognizer.error_occurred.connect(self._on_whisper_wake_error)
        self._whisper_wake_recognizer.start()

    def _on_whisper_wake(self):
        self._state = self.WAKING
        self._last_voice_text = "在呢"
        self.update()
        self._voice.speak("在呢")
        self._voice.synthesis_done.connect(self._on_whisper_ack_done)

    def _on_whisper_ack_done(self):
        try:
            self._voice.synthesis_done.disconnect(self._on_whisper_ack_done)
        except TypeError:
            pass
        if not self._wake_word_mode or not self._whisper_wake_recognizer:
            return
        self._state = self.LISTENING
        self.update()
        self._whisper_wake_recognizer.listen_for_command()

    def _on_whisper_command(self, text: str):
        text = text.strip()
        if not text:
            return
        if self._check_exit(text):
            return
        self._last_voice_text = text
        self.update()
        self._in_conversation = True
        self._query_ai(text)

    def _on_whisper_status(self, status: str):
        try:
            print(f"[Whisper Status] {status}")
        except OSError:
            pass
        self._last_voice_text = status
        self.update()
        if status == "唤醒监听中...":
            try:
                print("[Wake] Whisper 就绪，切换到 Whisper 唤醒")
            except OSError:
                pass
            if self._voice.is_listening():
                self._voice.stop_listening()

    def _on_whisper_wake_error(self, error: str):
        self._whisper_wake_recognizer = None
        self._last_voice_text = error
        self.update()
        if self._wake_word_mode:
            QTimer.singleShot(1000, self._start_wake_listen)

    def _on_wake_ack_done(self):
        try:
            self._voice.synthesis_done.disconnect(self._on_wake_ack_done)
        except TypeError:
            pass
        if not self._wake_word_mode:
            self._wake_pending = False
            self._state = self.ACTIVE
            self.update()
            return
        self._state = self.LISTENING
        self.update()
        if self._voice.is_listening():
            self._voice.stop_listening()
        QTimer.singleShot(300, lambda: self._voice.start_listening(timeout=6.0))

    def _on_voice_error(self, error: str):
        print(f"[Voice Error] {error}")
        self._last_voice_text = error
        self._state = self.ACTIVE
        self.update()
        if self._wake_word_mode and not self._whisper_wake_recognizer:
            QTimer.singleShot(500, self._start_wake_listen)
