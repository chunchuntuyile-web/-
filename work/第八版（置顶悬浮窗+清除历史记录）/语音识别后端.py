import os
import time
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from io import BytesIO
from flask import send_file
app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域携带 cookie

# ================= 配置 =================
# 数据库文件会保存在当前目录下
app.config['SECRET_KEY'] = 'your-secret-key-123456'  # 用于加密 cookie，随便写
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voice_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


# ================= 数据库模型 =================

# 1. 用户表
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


# 2. 历史记录表
class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_text = db.Column(db.Text, nullable=False)  # 用户说的话
    translated_text = db.Column(db.Text, nullable=False)  # 翻译结果
    detected_lang = db.Column(db.String(10))  # 识别到的语言
    target_lang = db.Column(db.String(10))  # 目标语言
    timestamp = db.Column(db.DateTime, default=datetime.now)  # 时间戳


# ================= AI 模型加载 (保持不变) =================
print("🚀 正在加载 AI 模型...")
# 显存够大可以用 large-v3，不够改用 small
asr_model = WhisperModel("large-v3", device="cuda", compute_type="int8")
mt_model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(mt_model_name)
mt_model = AutoModelForSeq2SeqLM.from_pretrained(mt_model_name).to("cuda")

LANG_MAP = {'zh': 'zho_Hans', 'en': 'eng_Latn', 'ja': 'jpn_Jpan', 'ko': 'kor_Hang',
            'fr': 'fra_Latn', 'de': 'deu_Latn', 'ru': 'rus_Cyrl', 'es': 'spa_Latn'}


# ================= 辅助函数 =================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def translate_nllb(text, src_code, tgt_code):
    if not text: return ""
    tokenizer.src_lang = src_code
    inputs = tokenizer(text, return_tensors="pt").to("cuda")
    target_lang_id = tokenizer.convert_tokens_to_ids(tgt_code)
    translated_tokens = mt_model.generate(**inputs, forced_bos_token_id=target_lang_id, max_length=100)
    return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]


# ================= 用户系统 API =================

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400

    # 创建新用户
    new_user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': '注册成功'}), 200

@app.route('/')
def index():
    # 确保你的 html 文件名是对的。如果是叫 "前端.html"，这里就写 "前端.html"
    return send_file('前端.html')
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    # 获取前端传来的登录类型：'user' 或 'admin'
    login_type = data.get('login_type', 'user')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # --- 核心拦截逻辑 ---
        if login_type == 'admin' and not user.is_admin:
            return jsonify({'error': '权限越界：该账号不是管理员'}), 403

        if login_type == 'user' and user.is_admin:
            return jsonify({'error': '请切换至【管理员登录】入口'}), 403
        # --------------------

        login_user(user)  # 记录登录状态
        return jsonify({'message': '登录成功', 'is_admin': user.is_admin})

    return jsonify({'error': '用户名或密码错误'}), 401


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': '已退出登录'})


@app.route('/get_history', methods=['GET'])
@login_required
def get_history():
    """获取历史记录：管理员看所有，普通用户看自己"""
    if current_user.is_admin:
        # 管理员：查询所有记录，并按时间倒序
        records = History.query.order_by(History.timestamp.desc()).all()
    else:
        # 普通用户：只查自己的 user_id
        records = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).all()

    # 格式化输出
    data = []
    for r in records:
        # 如果是管理员，额外显示这条记录是谁的
        owner_name = User.query.get(r.user_id).username if current_user.is_admin else "Me"
        data.append({
            'user': owner_name,
            'source': r.source_text,
            'target': r.translated_text,
            'lang': r.detected_lang,
            'time': r.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(data)


@app.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard_data():
    """获取管理员大盘的统计数据"""
    if not current_user.is_admin:
        return jsonify({'error': '无权限访问'}), 403

    records = History.query.all()

    # 1. 核心总指标
    total_users = User.query.count()
    total_records = len(records)

    # 2. 统计目标语言占比 (用于饼图)
    lang_stats = {}
    for r in records:
        # 为了展示好看，将简码映射为可读文字
        lang_name = "中文" if r.target_lang == "zho_Hans" else \
            "英文" if r.target_lang == "eng_Latn" else \
                "日文" if r.target_lang == "jpn_Jpan" else \
                    "韩文" if r.target_lang == "kor_Hang" else r.target_lang
        lang_stats[lang_name] = lang_stats.get(lang_name, 0) + 1

    pie_data = [{"name": k, "value": v} for k, v in lang_stats.items()]

    # 3. 按日期统计调用次数 (用于折线图)
    date_stats = {}
    for r in records:
        date_str = r.timestamp.strftime('%Y-%m-%d')
        date_stats[date_str] = date_stats.get(date_str, 0) + 1

    # 按日期排序
    sorted_dates = sorted(date_stats.keys())
    line_data = [date_stats[d] for d in sorted_dates]

    return jsonify({
        'total_users': total_users,
        'total_translations': total_records,
        'pie_data': pie_data,
        'line_dates': sorted_dates,
        'line_data': line_data
    })

@app.route('/export_history', methods=['GET'])
@login_required
def export_history():
    try:
        # 1. 根据权限查询数据 (逻辑同 get_history)
        if current_user.is_admin:
            records = History.query.order_by(History.timestamp.desc()).all()
        else:
            records = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).all()

        # 2. 将数据库对象转换为列表字典
        data_list = []
        for r in records:
            # 如果是管理员，查一下用户名；如果是普通用户，直接填自己
            if current_user.is_admin:
                owner = User.query.get(r.user_id)
                username = owner.username if owner else "Unknown"
            else:
                username = current_user.username

            data_list.append({
                "记录ID": r.id,
                "用户名": username,
                "源语言": r.detected_lang,
                "源文本": r.source_text,
                "目标语言": r.target_lang,
                "翻译结果": r.translated_text,
                "时间": r.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })

        # 3. 使用 Pandas 创建 DataFrame
        if not data_list:
            return jsonify({'error': '当前没有历史记录可导出'}), 404

        df = pd.DataFrame(data_list)

        # 4. 写入内存 (不产生临时文件)
        output = BytesIO()
        # 使用 openpyxl 引擎写入
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='语音历史记录')

            # (可选) 简单的列宽调整
            worksheet = writer.sheets['语音历史记录']
            worksheet.column_dimensions['B'].width = 15  # 用户名
            worksheet.column_dimensions['D'].width = 50  # 源文本
            worksheet.column_dimensions['F'].width = 50  # 翻译结果
            worksheet.column_dimensions['G'].width = 20  # 时间

        output.seek(0)

        # 5. 生成文件名 (带时间戳)
        filename = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # 6. 发送文件
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"Export Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    """清空历史记录接口"""
    try:
        if current_user.is_admin:
            # 如果是管理员，清空 History 表里的所有数据
            db.session.query(History).delete()
        else:
            # 如果是普通用户，只删除 user_id 是自己的数据
            History.query.filter_by(user_id=current_user.id).delete()

        # 提交更改到数据库
        db.session.commit()
        return jsonify({'message': '历史记录已成功清空！'})

    except Exception as e:
        db.session.rollback()  # 如果报错，撤销数据库操作
        print(f"Clear History Error: {e}")
        return jsonify({'error': str(e)}), 500
# ================= 核心业务 API =================

@app.route('/process_audio', methods=['POST'])
@login_required
def process_audio():
    filename = None  # 先声明变量
    try:
        if 'audio' not in request.files: return jsonify({'error': 'No audio'}), 400

        audio_file = request.files['audio']
        target_lang_code = request.form.get('target_lang', 'eng_Latn')

        filename = f"temp_{uuid.uuid4()}.webm"
        audio_file.save(filename)

        start_t = time.time()

        # --- 核心修复 1：开启 VAD 过滤静音，干掉 Nicolai Winther ---
        # vad_filter=True: 开启人声检测
        # min_silence_duration_ms=500: 小于0.5秒的声音忽略
        segments, info = asr_model.transcribe(
            filename,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        detected_lang = info.language
        src_text = "".join([s.text for s in segments])

        # 如果 VAD 判定为静音，src_text 会是空的，直接返回
        if not src_text.strip():
            return jsonify({'error': '静音', 'source_text': ''})

        nllb_src_code = LANG_MAP.get(detected_lang, 'eng_Latn')

        # 2. 翻译 (原有逻辑)
        zh_supplement = None
        final_text = ""

        if detected_lang == 'zh':
            final_text = translate_nllb(src_text, 'zho_Hans', target_lang_code)
        else:
            zh_supplement = translate_nllb(src_text, nllb_src_code, 'zho_Hans')
            final_text = zh_supplement if target_lang_code == 'zho_Hans' else translate_nllb(src_text, nllb_src_code,
                                                                                             target_lang_code)

        # 3. 存入数据库 (原有逻辑)
        if src_text.strip():
            record = History(user_id=current_user.id, source_text=src_text, translated_text=final_text,
                             detected_lang=detected_lang, target_lang=target_lang_code)
            db.session.add(record)
            db.session.commit()

        return jsonify({
            'detected_lang': detected_lang,
            'source_text': src_text,
            'zh_supplement': zh_supplement,
            'target_translated_text': final_text,
            'process_time': f"{time.time() - start_t:.2f}s"
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        # --- 核心修复 2：无论如何，最后一定删除临时音频文件 ---
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass


# ================= 初始化 =================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 第一次运行会自动创建 voice_app.db

        # 检查并创建管理员账号 (如果不存在)
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("👑 正在创建初始管理员账号...")
            # 这里设置管理员密码，例如 'admin123'
            hashed_pw = generate_password_hash('admin123')
            admin_user = User(username='admin', password_hash=hashed_pw, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            print("✅ 管理员创建成功: 账号 admin / 密码 admin123")

    app.run(host='0.0.0.0', port=5000)