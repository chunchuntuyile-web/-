import speech_recognition as sr
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import pyttsx3
import torch
import time


class ProTranslator:
    def __init__(self):
        print("🚀 正在初始化 RTX 3060 高性能模式...")

        # -----------------------------------------------------------
        # 1. 升级 ASR: 使用 Whisper Large-v3 (INT8 量化)
        # -----------------------------------------------------------
        # 'large-v3' 是目前 OpenAI 最强的开源模型
        # compute_type="int8" 是 3060 运行 Large 模型的关键，几乎不损失精度但显存减半
        print("正在加载 Whisper Large-v3 (这可能需要几分钟下载)...")
        self.asr_model = WhisperModel("large-v3", device="cuda", compute_type="int8")

        # -----------------------------------------------------------
        # 2. 升级 MT: 使用 Meta NLLB-200 (600M 参数版)
        # -----------------------------------------------------------
        print("正在加载 NLLB-200 翻译模型...")
        # 这里的 600M 模型比之前的 Helsinki 强大得多，支持 200 种语言互译
        model_name = "facebook/nllb-200-distilled-600M"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.mt_model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to("cuda")

        # 3. 初始化 TTS
        #self.tts_engine = pyttsx3.init()
        #self.tts_engine.setProperty('rate', 150)

        print("\n✅ 系统就绪！高性能模式已开启 (使用 CUDA)")

    def recognize_speech(self, audio_data):
        """语音识别 (高精度)"""
        # 保存临时文件
        with open("temp.wav", "wb") as f:
            f.write(audio_data.get_wav_data())

        # beam_size=5 增加搜索宽度，提高准确率
        segments, _ = self.asr_model.transcribe(
            "temp.wav",
            language="zh",
            beam_size=5,
            vad_filter=True  # 开启内置 VAD 过滤静音
        )
        text = "".join([s.text for s in segments])
        return text

    def translate_text(self, text):
        """机器翻译 (NLLB) - 修复版"""
        if not text: return ""

        # 1. 设定源语言 (这是 NLLB 的关键，必须告诉它是中文)
        self.tokenizer.src_lang = "zho_Hans"

        # 2. 编码文本
        inputs = self.tokenizer(text, return_tensors="pt").to("cuda")

        # 3. 获取目标语言的 ID (这里修复了报错)
        # 我们直接让分词器把 "eng_Latn" 转换成对应的数字 ID
        target_lang_id = self.tokenizer.convert_tokens_to_ids("eng_Latn")

        # 4. 生成翻译
        translated_tokens = self.mt_model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,  # 强制以英文开头
            max_length=100
        )

        result = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        return result

    def speak(self, text):
        """朗读文本 (修复版：每次重新初始化)"""
        print(f"🤖 机器: {text}")

        # 1. 每次说话前临时创建一个新的引擎
        engine = pyttsx3.init()

        # 2. 设置属性 (可以在这里调语速)
        engine.setProperty('rate', 150)

        # 3. 说话
        engine.say(text)

        # 4. 运行并等待 (这是关键，说完这句，这个 engine 也就完成使命了)
        engine.runAndWait()

        # 5. 显式停止 (防止占用音频通道)
        engine.stop()

    def run(self):
        recognizer = sr.Recognizer()
        # 提高灵敏度
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        with sr.Microphone() as source:
            print("正在校准环境噪音...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

        while True:
            try:
                with sr.Microphone() as source:
                    print("\n🎤 [高精度聆听中] 请说话...")
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=15)

                start_t = time.time()

                # 1. 识别
                zh_text = self.recognize_speech(audio)
                if not zh_text.strip(): continue
                print(f"📝 用户: {zh_text}")

                # 2. 翻译
                en_text = self.translate_text(zh_text)
                print(f"🔄 翻译: {en_text}")

                print(f"⚡ 耗时: {time.time() - start_t:.2f}s")

                # 3. 朗读
                self.speak(en_text)

            except Exception as e:
                print(f"⚠️ 发生错误 (但这不影响下次识别): {e}")


if __name__ == "__main__":
    app = ProTranslator()
    app.run()