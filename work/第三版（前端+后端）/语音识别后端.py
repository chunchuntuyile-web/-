import os
import time
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

app = Flask(__name__)
CORS(app)

print("🚀 正在加载模型，请稍候...")

# 1. ASR 模型
asr_model = WhisperModel("large-v3", device="cuda", compute_type="int8")

# 2. MT 模型
mt_model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(mt_model_name)
mt_model = AutoModelForSeq2SeqLM.from_pretrained(mt_model_name).to("cuda")

# 3. 语言代码映射表 (Whisper检测出的简写 -> NLLB需要的全称)
# 你可以在这里添加更多语言支持
LANG_MAP = {
    'zh': 'zho_Hans',  # 中文
    'en': 'eng_Latn',  # 英语
    'ja': 'jpn_Jpan',  # 日语
    'ko': 'kor_Hang',  # 韩语
    'fr': 'fra_Latn',  # 法语
    'de': 'deu_Latn',  # 德语
    'ru': 'rus_Cyrl',  # 俄语
    'es': 'spa_Latn'  # 西班牙语
}

print("✅ 服务端已就绪...")


def translate_nllb(text, src_code, tgt_code):
    """通用的翻译函数"""
    if not text: return ""

    # 动态设定源语言
    tokenizer.src_lang = src_code

    inputs = tokenizer(text, return_tensors="pt").to("cuda")
    target_lang_id = tokenizer.convert_tokens_to_ids(tgt_code)

    translated_tokens = mt_model.generate(
        **inputs,
        forced_bos_token_id=target_lang_id,
        max_length=100
    )
    return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]


@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        target_lang_code = request.form.get('target_lang', 'eng_Latn')

        filename = f"temp_{uuid.uuid4()}.webm"
        audio_file.save(filename)

        start_t = time.time()

        # --- 1. 智能语音识别 (ASR) ---
        # 移除 language="zh"，让模型自动检测语言
        segments, info = asr_model.transcribe(filename, beam_size=5)

        detected_lang = info.language  # 获取检测到的语言 (例如 'ko', 'zh', 'en')
        src_text = "".join([s.text for s in segments])

        # 获取 NLLB 对应的源语言代码，如果不在列表里，默认用英文处理
        nllb_src_code = LANG_MAP.get(detected_lang, 'eng_Latn')

        print(f"检测语言: {detected_lang} ({nllb_src_code}) -> 内容: {src_text}")

        # --- 2. 翻译逻辑 ---

        # 准备返回的数据包
        response_data = {
            'detected_lang': detected_lang,
            'source_text': src_text,  # 原文
            'zh_supplement': None,  # 中文辅助翻译 (仅当原文不是中文时有值)
            'target_translated_text': "",  # 最终目标语言翻译
            'process_time': ""
        }

        # 场景 A: 用户说的是中文
        if detected_lang == 'zh':
            # 直接翻译成目标语言
            response_data['target_translated_text'] = translate_nllb(src_text, 'zho_Hans', target_lang_code)

        # 场景 B: 用户说的是外语 (比如韩语)
        else:
            # 1. 先翻译成中文 (为了让你看懂)
            response_data['zh_supplement'] = translate_nllb(src_text, nllb_src_code, 'zho_Hans')

            # 2. 再翻译成目标语言 (为了播放和输出)
            # 如果目标语言就是中文，那直接用上面的结果，不用翻两次
            if target_lang_code == 'zho_Hans':
                response_data['target_translated_text'] = response_data['zh_supplement']
            else:
                response_data['target_translated_text'] = translate_nllb(src_text, nllb_src_code, target_lang_code)

        os.remove(filename)
        response_data['process_time'] = f"{time.time() - start_t:.2f}s"

        return jsonify(response_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)