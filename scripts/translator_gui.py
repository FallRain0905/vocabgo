#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocabGo 翻译助手 - GUI版本
功能：语音识别 + 自动翻译，Translumo 风格界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import requests
import sys
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ================= 配置加载 =================
CONFIG_FILE = project_root / "config" / "qwen-config.json"

def load_config():
    """加载配置"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

config = load_config()
if not config:
    print("❌ 配置文件加载失败")
    sys.exit(1)

# API 配置
LLM_API_URL = config.get("api_url", "")
LLM_API_KEY = config.get("api_key", "")
LLM_MODEL = config.get("model", "qwen-plus")

# 语音识别 API 选择
SPEECH_API = config.get("speech_api", "aliyun")
ALIYUN_APPKEY = config.get("aliyun_appkey", "")
ALIYUN_TOKEN = config.get("aliyun_token", "")

# 录音参数
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 0.02
SILENCE_DURATION = 1.0
MAX_DURATION = 5.0

# ================= 音频录制类 =================
class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.silence_start = None
        self.start_time = None

    def callback(self, indata, frames, time_info, status):
        """音频流回调"""
        if self.recording:
            self.audio_data.extend(indata.tolist())

        volume = np.max(np.abs(indata))

        if volume > SILENCE_THRESHOLD:
            if not self.recording:
                self.recording = True
                self.audio_data.extend(indata.tolist())
                self.start_time = time.time()
            self.silence_start = None
        else:
            if self.recording and self.silence_start is None:
                self.silence_start = time.time()
            elif self.recording and self.silence_start and (time.time() - self.silence_start) > SILENCE_DURATION:
                self.recording = False

    def record_until_silence(self):
        """录音直到静音"""
        self.audio_data = []
        self.silence_start = None
        self.start_time = None
        self.recording = False

        with sd.InputStream(callback=self.callback,
                         channels=CHANNELS,
                         samplerate=SAMPLE_RATE):
            while True:
                if not self.recording and len(self.audio_data) > 0:
                    break
                if len(self.audio_data) > SAMPLE_RATE * MAX_DURATION * CHANNELS:
                    break
                time.sleep(0.01)

        if self.audio_data:
            return np.array(self.audio_data, dtype=np.float32)
        return None

# ================= 语音识别类 =================
class SpeechRecognizer:
    def __init__(self):
        self.aliyun_token = ALIYUN_TOKEN

    def recognize_aliyun(self, audio_data):
        """阿里云语音识别"""
        if not ALIYUN_APPKEY:
            print("阿里云 AppKey 未配置")
            return None

        # 保存音频到临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
            sf.write(f, audio_data, SAMPLE_RATE)

        try:
            # 阿里云一句话识别 API
            url = f"https://nls-gateway.aliyuncs.com/stream/v1/asr?appkey={ALIYUN_APPKEY}"

            with open(temp_file, 'rb') as f:
                audio_data_bytes = f.read()

            headers = {
                'Content-Type': 'audio/wav; samplerate=16000',
                'X-NLS-Token': self.aliyun_token
            }

            response = requests.post(url, headers=headers, data=audio_data_bytes, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get('status') == 20000000:
                return result.get('result', '')
            else:
                print(f"阿里云识别错误: {result.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"阿里云识别失败: {e}")
            return None
        finally:
            try:
                os.remove(temp_file)
            except:
                pass

    def recognize(self, audio_data):
        """语音识别"""
        return self.recognize_aliyun(audio_data)

# ================= 翻译类 =================
class Translator:
    def __init__(self):
        self.cache = {}  # 翻译缓存

    def translate(self, english_text):
        """调用大模型翻译"""
        # 检查缓存
        if english_text.lower() in self.cache:
            cached = self.cache[english_text.lower()]
            return f"{cached} (缓存)"

        if not LLM_API_KEY or LLM_API_KEY.startswith("YOUR"):
            return "⚠️ API Key 未配置"

        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个极速翻译引擎。请直接给出英文单词或短语的中文意思，不要解释，不要标点。"},
                {"role": "user", "content": english_text}
            ],
            "temperature": config.get("temperature", 0.1),
            "max_tokens": config.get("max_tokens", 100)
        }

        try:
            response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()

            if "choices" in result:
                translation = result['choices'][0]['message']['content'].strip()
            elif "output" in result:
                translation = result['output']['text'].strip()
            else:
                return "❌ 翻译失败"

            # 缓存结果
            self.cache[english_text.lower()] = translation
            return translation
        except Exception as e:
            print(f"翻译失败: {e}")
            return "❌ 翻译失败"

# ================= GUI 主窗口 =================
class TranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VocabGo 翻译助手")
        self.root.attributes('-topmost', True)  # 置顶

        # 窗口大小和位置
        self.root.geometry("500x450+100+100")
        self.root.configure(bg='#2D2D2D')

        # 可拖拽
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.do_move)

        # 初始化组件
        self.recorder = AudioRecorder()
        self.recognizer = SpeechRecognizer()
        self.translator = Translator()

        # 创建界面
        self.create_widgets()

        # 自动启动录音
        self.start_listening()

    def create_widgets(self):
        """创建界面组件"""

        # 标题栏
        title_frame = tk.Frame(self.root, bg='#3D3D3D', height=30)
        title_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            title_frame,
            text="🎧 语音识别翻译",
            bg='#3D3D3D',
            fg='white',
            font=('Arial', 12, 'bold')
        )
        title_label.pack(pady=5)

        # 主内容区域
        main_frame = tk.Frame(self.root, bg='#2D2D2D', padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 英文显示区域
        tk.Label(
            main_frame,
            text="🇺🇸 英文识别",
            bg='#2D2D2D',
            fg='#4FC3F7',
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))

        self.english_text = scrolledtext.ScrolledText(
            main_frame,
            height=5,
            bg='#3D3D3D',
            fg='white',
            font=('Arial', 14),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.english_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 中文显示区域
        tk.Label(
            main_frame,
            text="🇨🇳 中文翻译",
            bg='#2D2D2D',
            fg='#FFA726',
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))

        self.chinese_text = scrolledtext.ScrolledText(
            main_frame,
            height=5,
            bg='#3D3D3D',
            fg='white',
            font=('SimHei', 14),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.chinese_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 状态栏
        status_frame = tk.Frame(main_frame, bg='#2D2D2D')
        status_frame.pack(fill=tk.X)

        self.status_label = tk.Label(
            status_frame,
            text="🔴 等待音频...",
            bg='#2D2D2D',
            fg='#9E9E9E',
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT)

        # 按钮区域
        button_frame = tk.Frame(self.root, bg='#3D3D3D', height=40)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # 暂停/继续按钮
        self.pause_button = tk.Button(
            button_frame,
            text="⏸️ 暂停",
            bg='#FF5722',
            fg='white',
            font=('Arial', 9),
            command=self.toggle_pause,
            relief=tk.FLAT
        )
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 清空按钮
        clear_button = tk.Button(
            button_frame,
            text="🗑️ 清空",
            bg='#9E9E9E',
            fg='white',
            font=('Arial', 9),
            command=self.clear_text,
            relief=tk.FLAT
        )
        clear_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 设置透明度
        opacity_frame = tk.Frame(button_frame, bg='#3D3D3D')
        opacity_frame.pack(side=tk.RIGHT, padx=5)

        tk.Label(
            opacity_frame,
            text="透明度:",
            bg='#3D3D3D',
            fg='white',
            font=('Arial', 8)
        ).pack(side=tk.LEFT)

        self.opacity_scale = tk.Scale(
            opacity_frame,
            from_=60, to=100,
            orient=tk.HORIZONTAL,
            bg='#3D3D3D',
            fg='white',
            length=100,
            command=self.update_opacity
        )
        self.opacity_scale.set(90)
        self.opacity_scale.pack(side=tk.LEFT, padx=5)

        # 设置按钮
        settings_button = tk.Button(
            button_frame,
            text="⚙️ 设置",
            bg='#607D8B',
            fg='white',
            font=('Arial', 9),
            command=self.open_settings,
            relief=tk.FLAT
        )
        settings_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 窗口置顶切换
        self.topmost_var = tk.BooleanVar(value=True)
        topmost_check = tk.Checkbutton(
            button_frame,
            text="置顶",
            variable=self.topmost_var,
            command=self.toggle_topmost,
            bg='#3D3D3D',
            fg='white',
            selectcolor='#4CAF50',
            activebackground='#3D3D3D'
        )
        topmost_check.pack(side=tk.RIGHT, padx=5)

    def start_move(self, event):
        """开始拖拽"""
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        """拖拽窗口"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def update_opacity(self, value):
        """更新透明度"""
        self.root.attributes('-alpha', float(value) / 100)

    def toggle_topmost(self):
        """切换置顶"""
        if self.topmost_var.get():
            self.root.attributes('-topmost', True)
        else:
            self.root.attributes('-topmost', False)

    def toggle_pause(self):
        """暂停/继续"""
        if hasattr(self, 'is_paused'):
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.pause_button.config(text="▶️ 继续", bg='#4CAF50')
                self.update_status("⏸️ 已暂停")
            else:
                self.pause_button.config(text="⏸️ 暂停", bg='#FF5722')
                self.update_status("🟢 继续监听...")
        else:
            self.is_paused = False
            self.pause_button.config(text="⏸️ 暂停", bg='#FF5722')

    def clear_text(self):
        """清空文本"""
        self.english_text.delete(1.0, tk.END)
        self.chinese_text.delete(1.0, tk.END)

    def update_status(self, status):
        """更新状态"""
        self.status_label.config(text=status)

    def start_listening(self):
        """开始监听"""
        def listen_loop():
            while True:
                if hasattr(self, 'is_paused') and self.is_paused:
                    time.sleep(0.1)
                    continue

                try:
                    self.update_status("🟢 正在监听...")
                    audio_data = self.recorder.record_until_silence()

                    if audio_data is not None:
                        self.update_status("🔄 正在识别...")
                        english = self.recognizer.recognize(audio_data)

                        if english:
                            self.update_status("🧠 正在翻译...")

                            # 更新英文显示
                            self.root.after(0, lambda: self.english_text.delete(1.0, tk.END))
                            self.root.after(0, lambda: self.english_text.insert(tk.END, english))

                            # 翻译
                            chinese = self.translator.translate(english)

                            # 更新中文显示
                            self.root.after(0, lambda: self.chinese_text.delete(1.0, tk.END))
                            self.root.after(0, lambda: self.chinese_text.insert(tk.END, chinese))

                            self.update_status("✅ 识别完成")
                        else:
                            self.update_status("❌ 识别失败")

                    time.sleep(0.5)

                except Exception as e:
                    self.update_status(f"❌ 错误: {str(e)[:30]}")
                    time.sleep(1)

        threading.Thread(target=listen_loop, daemon=True).start()

    def open_settings(self):
        """打开设置窗口"""
        SettingsWindow(self.root, self.apply_settings)

    def apply_settings(self, settings):
        """应用设置"""
        global SPEECH_API, ALIYUN_APPKEY, ALIYUN_TOKEN, LLM_API_KEY, LLM_MODEL
        global config

        SPEECH_API = settings.get('speech_api', 'aliyun')
        ALIYUN_APPKEY = settings.get('aliyun_appkey', '')
        ALIYUN_TOKEN = settings.get('aliyun_token', '')
        LLM_API_KEY = settings.get('api_key', '')
        LLM_MODEL = settings.get('model', 'qwen-plus')

        config['speech_api'] = SPEECH_API
        config['aliyun_appkey'] = ALIYUN_APPKEY
        config['aliyun_token'] = ALIYUN_TOKEN
        config['api_key'] = LLM_API_KEY
        config['model'] = LLM_MODEL

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        self.root.title("VocabGo 翻译助手")
        self.translator.cache = {}
        messagebox.showinfo("设置", "设置已保存！\n部分设置需要重启应用生效。")

class SettingsWindow:
    def __init__(self, parent, apply_callback):
        self.parent = parent
        self.apply_callback = apply_callback

        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("500x600+200+100")
        self.window.configure(bg='#2D2D2D')
        self.window.transient(parent)
        self.window.grab_set()

        self.speech_api_var = tk.StringVar(value=SPEECH_API)
        self.aliyun_appkey_var = tk.StringVar(value=ALIYUN_APPKEY)
        self.aliyun_token_var = tk.StringVar(value=ALIYUN_TOKEN)
        self.llm_api_key_var = tk.StringVar(value=LLM_API_KEY)
        self.llm_model_var = tk.StringVar(value=LLM_MODEL)

        self.create_widgets()

    def create_widgets(self):
        title_frame = tk.Frame(self.window, bg='#3D3D3D', height=35)
        title_frame.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            title_frame,
            text="⚙️ 语音识别翻译设置",
            bg='#3D3D3D',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(pady=10)

        main_frame = tk.Frame(self.window, bg='#2D2D2D', padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_section(main_frame, "🎤 语音识别 API", 0)
        api_frame = tk.Frame(main_frame, bg='#2D2D2D')
        api_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Radiobutton(
            api_frame, text="阿里云语音识别", variable=self.speech_api_var,
            value="aliyun", bg='#2D2D2D', fg='white',
            selectcolor='#4CAF50', activebackground='#2D2D2D',
            font=('Arial', 10)
        ).pack(anchor=tk.W)

        self.create_section(main_frame, "☁️ 阿里云配置", 1)
        aliyun_frame = tk.Frame(main_frame, bg='#2D2D2D')
        aliyun_frame.pack(fill=tk.X, pady=(0, 15))

        self.create_input(aliyun_frame, "AppKey:", self.aliyun_appkey_var, 0)
        self.create_input(aliyun_frame, "Token (可选，留空自动获取):", self.aliyun_token_var, 1)

        self.create_section(main_frame, "🧠 通义千问配置", 2)
        llm_frame = tk.Frame(main_frame, bg='#2D2D2D')
        llm_frame.pack(fill=tk.X, pady=(0, 15))

        self.create_input(llm_frame, "API Key:", self.llm_api_key_var, 0)

        model_frame = tk.Frame(llm_frame, bg='#2D2D2D')
        model_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(
            model_frame, text="模型:", bg='#2D2D2D', fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)

        models = ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"]
        self.model_combobox = ttk.Combobox(
            model_frame, values=models, textvariable=self.llm_model_var,
            state="readonly", width=15
        )
        self.model_combobox.pack(side=tk.LEFT, padx=(10, 0))

        button_frame = tk.Frame(self.window, bg='#3D3D3D', height=50)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Button(
            button_frame, text="💾 保存", bg='#4CAF50', fg='white',
            font=('Arial', 10, 'bold'), width=10, relief=tk.FLAT,
            command=self.save_settings
        ).pack(side=tk.LEFT, padx=15, pady=10)

        tk.Button(
            button_frame, text="❌ 取消", bg='#F44336', fg='white',
            font=('Arial', 10, 'bold'), width=10, relief=tk.FLAT,
            command=self.window.destroy
        ).pack(side=tk.LEFT, padx=15, pady=10)

    def create_section(self, parent, title, section_num):
        section_frame = tk.Frame(parent, bg='#2D2D2D')
        section_frame.pack(fill=tk.X, pady=(10 if section_num == 0 else 15, 0))

        tk.Label(
            section_frame, text=title, bg='#2D2D2D', fg='#FFA726',
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W)

    def create_input(self, parent, label, variable, padx):
        input_frame = tk.Frame(parent, bg='#2D2D2D')
        input_frame.pack(fill=tk.X, pady=(10 if padx == 0 else 5, 0), padx=padx)

        tk.Label(
            input_frame, text=label, bg='#2D2D2D', fg='white',
            font=('Arial', 9), width=20, anchor=tk.W
        ).pack(side=tk.LEFT)

        entry = tk.Entry(
            input_frame, textvariable=variable, bg='#3D3D3D', fg='white',
            font=('Arial', 10), relief=tk.FLAT, show='*' if 'Key' in label or 'Token' in label else ''
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

    def save_settings(self):
        settings = {
            'speech_api': self.speech_api_var.get(),
            'aliyun_appkey': self.aliyun_appkey_var.get(),
            'aliyun_token': self.aliyun_token_var.get(),
            'api_key': self.llm_api_key_var.get(),
            'model': self.llm_model_var.get()
        }

        if settings['speech_api'] == "aliyun" and not settings['aliyun_appkey']:
            messagebox.showerror("错误", "请输入阿里云 AppKey！")
            return

        if not settings['api_key']:
            messagebox.showerror("错误", "请输入通义千问 API Key！")
            return

        self.apply_callback(settings)
        self.window.destroy()

# ================= 主函数 =================
def main():
    root = tk.Tk()
    app = TranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
