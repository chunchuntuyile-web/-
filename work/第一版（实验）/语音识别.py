import speech_recognition as sr
from faster_whisper import WhisperModel
from transformers import MarianMTModel, MarianTokenizer
import pyttsx3
import time


class LocalTranslator:
    def __init__(self):
        print("正在初始化系统模型，请稍候...")

        # 1. 初始化 ASR (语音识别) - 使用 faster-whisper
        # model_size 可选: "tiny", "base", "small" (越大越准但越慢)
        # device 可选: "cuda" (N卡) 或 "cpu"
        self.asr_model = WhisperModel("base", device="cuda", compute_type="int8")

        # 2. 初始化 MT (机器翻译) - 中文转英文
        # 使用赫尔辛基大学的轻量级模型
        model_name = "Helsinki-NLP/opus-mt-zh-en"
        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        self.mt_model = MarianMTModel.from_pretrained(model_name)

        # 3. 初始化 TTS (语音合成)
        self.tts_engine = pyttsx3.init()
        # 设置语速
        self.tts_engine.setProperty('rate', 150)

        print(">>> 系统就绪！请开始说话...")

    def recognize_speech(self, audio_data):
        """将音频数据保存临时文件并识别"""
        # 为了简单，SpeechRecognition 的数据先存为 wav，再给 Whisper 读取
        with open("../temp.wav", "wb") as f:
            f.write(audio_data.get_wav_data())

        segments, _ = self.asr_model.transcribe("temp.wav", language="zh")
        text = "".join([s.text for s in segments])
        return text

    def translate_text(self, text):
        """文本翻译"""
        if not text: return ""
        inputs = self.tokenizer(text, return_tensors="pt", padding=True)
        translated = self.mt_model.generate(**inputs)
        result = self.tokenizer.decode(translated[0], skip_special_tokens=True)
        return result

    def speak(self, text):
        """朗读文本"""
        print(f"机器: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def run(self):
        recognizer = sr.Recognizer()
        # 动态调整环境噪音阈值
        with sr.Microphone() as source:
            print("正在校准环境噪音...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

        while True:
            try:
                with sr.Microphone() as source:
                    print("\n[听] 正在聆听... (说完话请停顿)")
                    # listen会自动检测静音来停止录音
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

                print("[处理] 正在识别...")
                start_t = time.time()

                # 1. 识别
                zh_text = self.recognize_speech(audio)
                if not zh_text.strip():
                    continue
                print(f"用户(中文): {zh_text}")

                # 2. 翻译
                en_text = self.translate_text(zh_text)
                print(f"翻译(英文): {en_text}")

                print(f"耗时: {time.time() - start_t:.2f}s")

                # 3. 朗读
                self.speak(en_text)

            except sr.WaitTimeoutError:
                print("超时，未检测到语音")
            except KeyboardInterrupt:
                print("程序退出")
                break
            except Exception as e:
                print(f"发生错误: {e}")


if __name__ == "__main__":
    app = LocalTranslator()
    app.run()