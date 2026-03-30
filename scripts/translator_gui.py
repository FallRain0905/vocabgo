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
from PIL import Image, ImageGrab, ImageDraw, ImageFont
import io
import base64
import keyboard  # 用于全局快捷键

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
BAI_DU_API_KEY = config.get("baidu_api_key", "")
BAI_DU_SECRET_KEY = config.get("baidu_secret_key", "")

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
        self.baidu_token = None
        self.aliyun_token = ALIYUN_TOKEN

    def get_baidu_token(self):
        """获取百度 Token"""
        if self.baidu_token:
            return self.baidu_token

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": BAI_DU_API_KEY,
            "client_secret": BAI_DU_SECRET_KEY
        }

        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()
            self.baidu_token = response.json()['access_token']
            return self.baidu_token
        except:
            return None

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

    def recognize_baidu(self, audio_data):
        """百度语音识别"""
        token = self.get_baidu_token()
        if not token:
            return None

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
            sf.write(f, audio_data, SAMPLE_RATE)

        try:
            url = "https://vop.baidu.com/server_api"
            params = {
                "dev_pid": 1737,
                "token": token,
                "format": "wav",
                "rate": 16000,
                "cuid": "vocabgo_rpa_001"
            }

            with open(temp_file, 'rb') as f:
                audio_data_bytes = f.read()

            headers = {
                'Content-Type': 'audio/wav; rate=16000',
                'Content-Length': str(len(audio_data_bytes))
            }

            response = requests.post(url, params=params, headers=headers, data=audio_data_bytes, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get('err_no') == 0:
                return result.get('result', [''])[0]
        except Exception as e:
            print(f"百度识别失败: {e}")
        finally:
            try:
                os.remove(temp_file)
            except:
                pass

        return None

    def recognize(self, audio_data):
        """语音识别（根据配置选择API）"""
        if SPEECH_API == "aliyun":
            return self.recognize_aliyun(audio_data)
        else:
            return self.recognize_baidu(audio_data)

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

# ================= 百度 OCR 识别器 =================
class BaiduOCRRecognizer:
    def __init__(self):
        self.api_key = BAI_DU_API_KEY
        self.secret_key = BAI_DU_SECRET_KEY
        self.token = None
        self.available = bool(self.api_key and self.secret_key)

    def get_token(self):
        """获取百度 OCR Token"""
        if self.token:
            return self.token

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()
            self.token = response.json()['access_token']
            return self.token
        except Exception as e:
            print(f"百度 OCR Token 获取失败: {e}")
            return None

    def is_available(self):
        """检查 OCR 是否可用"""
        return self.available

    def recognize_sync(self, image):
        """同步 OCR 识别"""
        if not self.available:
            return "❌ 百度 OCR 未配置"

        token = self.get_token()
        if not token:
            return "❌ 百度 OCR Token 获取失败"

        try:
            # 将 PIL 图片转换为字节流
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            # Base64 编码
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # 百度 OCR API（通用文字识别）
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={token}"

            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {'image': img_base64}

            # 发送请求
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()

            result = response.json()

            # 提取识别结果
            if 'words_result' in result:
                words_result = result['words_result']
                text_lines = [word['words'] for word in words_result]
                return '\n'.join(text_lines) if text_lines else "❌ 未识别到文字"
            else:
                error_msg = result.get('error_msg', 'Unknown error')
                return f"❌ OCR 识别失败: {error_msg}"

        except Exception as e:
            print(f"OCR 识别失败: {e}")
            return f"❌ OCR 识别失败: {str(e)}"

# ================= OCR 区域选择窗口 =================
class OCRWindow:
    """类似 Translumo 的 OCR 窗口"""
    def __init__(self, parent, baidu_ocr, translator):
        self.parent = parent
        self.baidu_ocr = baidu_ocr
        self.translator = translator

        # 创建全屏窗口
        self.window = tk.Toplevel(parent)
        self.window.title("VocabGo OCR")
        self.window.geometry("800x600+300+100")
        self.window.attributes('-topmost', True)
        self.window.configure(bg='#2D2D2D')
        self.window.attributes('-alpha', 0.95)  # 稍微透明

        # 选择区域参数
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None
        self.is_selecting = False
        self.selected_coords = None  # (x1, y1, x2, y2)

        # 快捷键监听
        self.hotkey_registered = False
        self.window.bind("<Destroy>", self.on_destroy)

        # 创建界面
        self.create_widgets()

        # 注册快捷键
        self.register_hotkey()

    def create_widgets(self):
        """创建界面组件"""
        # 标题栏
        title_frame = tk.Frame(self.window, bg='#3D3D3D', height=30)
        title_frame.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            title_frame,
            text="🖼️ OCR 文字识别",
            bg='#3D3D3D',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(pady=5)

        # 提示信息
        info_frame = tk.Frame(self.window, bg='#2D2D2D', padx=10, pady=10)
        info_frame.pack(fill=tk.X)

        tk.Label(
            info_frame,
            text="📋 使用说明：\n"
                 "1. 点击'选择区域'按钮，用鼠标拖动选择屏幕区域\n"
                 "2. 按 `~` 键触发 OCR 识别\n"
                 "3. 识别结果会自动翻译",
            bg='#2D2D2D',
            fg='#9E9E9E',
            font=('SimHei', 9),
            justify=tk.LEFT
        ).pack(anchor=tk.W)

        # 主内容区域
        main_frame = tk.Frame(self.window, bg='#2D2D2D', padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 英文显示区域
        tk.Label(
            main_frame,
            text="🇺🇸 识别文字",
            bg='#2D2D2D',
            fg='#4FC3F7',
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))

        self.english_text = scrolledtext.ScrolledText(
            main_frame,
            height=6,
            bg='#3D3D3D',
            fg='white',
            font=('Arial', 12),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.english_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

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
            height=4,
            bg='#3D3D3D',
            fg='white',
            font=('SimHei', 12),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.chinese_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 状态栏
        status_frame = tk.Frame(main_frame, bg='#2D2D2D')
        status_frame.pack(fill=tk.X)

        self.status_label = tk.Label(
            status_frame,
            text="🟢 等待选择区域...",
            bg='#2D2D2D',
            fg='#9E9E9E',
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT)

        # 按钮区域
        button_frame = tk.Frame(self.window, bg='#3D3D3D', height=40)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # 选择区域按钮
        select_button = tk.Button(
            button_frame,
            text="📐 选择区域",
            bg='#4CAF50',
            fg='white',
            font=('Arial', 9),
            command=self.start_selection,
            relief=tk.FLAT
        )
        select_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 快捷键提示
        hotkey_label = tk.Label(
            button_frame,
            text="⌨️ 按 `~` 键识别",
            bg='#3D3D3D',
            fg='#9E9E9E',
            font=('Arial', 9)
        )
        hotkey_label.pack(side=tk.LEFT, padx=15)

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

        # 关闭按钮
        close_button = tk.Button(
            button_frame,
            text="❌ 关闭",
            bg='#F44336',
            fg='white',
            font=('Arial', 9),
            command=self.close,
            relief=tk.FLAT
        )
        close_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def register_hotkey(self):
        """注册快捷键"""
        try:
            keyboard.add_hotkey('`', self.trigger_ocr)
            self.hotkey_registered = True
            print("✅ 快捷键 `~` 已注册")
        except Exception as e:
            print(f"⚠️ 快捷键注册失败: {e}")
            self.hotkey_registered = False

    def on_destroy(self, event):
        """窗口销毁时清理"""
        if self.hotkey_registered:
            try:
                keyboard.remove_hotkey('`')
                print("✅ 快捷键已注销")
            except:
                pass

    def start_selection(self):
        """开始选择区域"""
        # 最小化当前窗口
        self.window.state('iconic')

        # 等待一小段时间让窗口最小化
        self.window.after(500, self.create_selection_window)

    def create_selection_window(self):
        """创建选择窗口"""
        self.selection_window = tk.Toplevel(self.window)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.configure(bg='black')
        self.selection_window.attributes('-topmost', True)
        self.selection_window.overrideredirect(True)

        # 创建画布
        self.canvas = tk.Canvas(
            self.selection_window,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标事件
        self.canvas.bind('<Button-1>', self.on_selection_start)
        self.canvas.bind('<B1-Motion>', self.on_selection_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_selection_end)
        self.canvas.bind('<Escape>', self.cancel_selection)

        # 显示提示
        self.canvas.create_text(
            self.selection_window.winfo_screenwidth() // 2,
            50,
            text="用鼠标拖动选择区域，按 ESC 取消",
            fill='white',
            font=('Arial', 16)
        )

    def on_selection_start(self, event):
        """开始拖动"""
        self.is_selecting = True
        self.selection_start = (event.x, event.y)
        self.selection_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline='red', width=2, fill='', stipple='gray25'
        )

    def on_selection_drag(self, event):
        """拖动中"""
        if self.is_selecting:
            self.selection_end = (event.x, event.y)
            self.canvas.coords(
                self.selection_rect,
                self.selection_start[0], self.selection_start[1],
                event.x, event.y
            )

    def on_selection_end(self, event):
        """结束选择"""
        if self.is_selecting:
            self.is_selecting = False
            self.selection_end = (event.x, event.y)

            # 计算选择区域
            x1 = min(self.selection_start[0], event.x)
            y1 = min(self.selection_start[1], event.y)
            x2 = max(self.selection_start[0], event.x)
            y2 = max(self.selection_start[1], event.y)

            # 保存选择区域
            self.selected_coords = (x1, y1, x2, y2)

            # 关闭选择窗口
            self.selection_window.destroy()

            # 恢复主窗口
            self.window.state('normal')
            self.window.deiconify()

            # 更新状态
            area_size = f"{x2-x1}x{y2-y1}"
            self.status_label.config(text=f"📐 已选择区域 ({area_size})，按 `~` 键识别")

    def cancel_selection(self, event):
        """取消选择"""
        self.is_selecting = False
        self.selected_coords = None
        self.selection_window.destroy()
        self.window.state('normal')
        self.window.deiconify()
        self.status_label.config(text="🟢 已取消，重新选择")

    def trigger_ocr(self):
        """触发 OCR 识别"""
        if not self.selected_coords:
            self.status_label.config(text="⚠️ 请先选择区域")
            return

        # 在后台线程中执行 OCR
        threading.Thread(target=self.perform_ocr, daemon=True).start()

    def perform_ocr(self):
        """执行 OCR 识别"""
        try:
            if not self.baidu_ocr.is_available():
                self.window.after(0, lambda: self.status_label.config(text="❌ OCR 不可用"))
                self.window.after(0, lambda: messagebox.showerror(
                    "OCR 配置错误",
                    "百度 OCR 需要 API Key 和 Secret Key\n\n请编辑配置文件：\nconfig/qwen-config.json\n\n确保已配置：\n- baidu_api_key\n- baidu_secret_key\n\n这些配置已在语音识别中使用，可以直接用于 OCR。\n\n详见文档：docs/08-ocr-integration.md"
                ))
                return

            self.window.after(0, lambda: self.status_label.config(text="🔄 正在识别..."))

            # 直接截取选择区域（使用 bbox 参数）
            x1, y1, x2, y2 = self.selected_coords
            cropped = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            # 执行 OCR
            extracted_text = self.baidu_ocr.recognize_sync(cropped)

            # 更新英文显示
            self.window.after(0, lambda: self.english_text.delete(1.0, tk.END))
            self.window.after(0, lambda: self.english_text.insert(tk.END, extracted_text))

            # 翻译
            if extracted_text and not extracted_text.startswith("❌"):
                first_line = extracted_text.split('\n')[0].strip()
                if first_line:
                    chinese = self.translator.translate(first_line)

                    # 更新中文显示
                    self.window.after(0, lambda: self.chinese_text.delete(1.0, tk.END))
                    self.window.after(0, lambda: self.chinese_text.insert(tk.END, chinese))

            self.window.after(0, lambda: self.status_label.config(text="✅ 识别完成"))

        except Exception as e:
            self.window.after(0, lambda: self.status_label.config(text=f"❌ 失败: {str(e)[:30]}"))

    def clear_text(self):
        """清空文本"""
        self.english_text.delete(1.0, tk.END)
        self.chinese_text.delete(1.0, tk.END)

    def close(self):
        """关闭窗口"""
        if self.hotkey_registered:
            try:
                keyboard.remove_hotkey('`')
            except:
                pass
        self.window.destroy()

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
        self.baidu_ocr = BaiduOCRRecognizer()

        # OCR 窗口
        self.ocr_window = None

        # 创建界面
        self.create_widgets()

        # 自动启动录音
        self.start_listening()

    def create_widgets(self):
        """创建界面组件"""

        # 标题栏
        title_frame = tk.Frame(self.root, bg='#3D3D3D', height=30)
        title_frame.pack(fill=tk.X, side=tk.TOP)

        api_name = "阿里云" if SPEECH_API == "aliyun" else "百度"
        title_label = tk.Label(
            title_frame,
            text=f"🎧 语音识别翻译 ({api_name})",
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

        # OCR 窗口按钮
        ocr_button = tk.Button(
            button_frame,
            text="🖼️ OCR",
            bg='#FFC107',
            fg='white',
            font=('Arial', 9),
            command=self.open_ocr_window,
            relief=tk.FLAT
        )
        ocr_button.pack(side=tk.LEFT, padx=5, pady=5)

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

    def open_ocr_window(self):
        """打开 OCR 窗口"""
        if self.ocr_window is None or not self.ocr_window.window.winfo_exists():
            self.ocr_window = OCRWindow(self.root, self.baidu_ocr, self.translator)

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

        api_name = "阿里云" if SPEECH_API == "aliyun" else "百度"
        self.root.title(f"VocabGo 翻译助手 ({api_name})")
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
        self.baidu_api_key_var = tk.StringVar(value=BAI_DU_API_KEY)
        self.baidu_secret_key_var = tk.StringVar(value=BAI_DU_SECRET_KEY)
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

        tk.Radiobutton(
            api_frame, text="百度语音识别", variable=self.speech_api_var,
            value="baidu", bg='#2D2D2D', fg='white',
            selectcolor='#4CAF50', activebackground='#2D2D2D',
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=(5, 0))

        if SPEECH_API == "aliyun":
            self.create_section(main_frame, "☁️ 阿里云配置", 1)
            aliyun_frame = tk.Frame(main_frame, bg='#2D2D2D')
            aliyun_frame.pack(fill=tk.X, pady=(0, 15))

            self.create_input(aliyun_frame, "AppKey:", self.aliyun_appkey_var, 0)
            self.create_input(aliyun_frame, "Token (可选，留空自动获取):", self.aliyun_token_var, 1)
        else:
            self.create_section(main_frame, "🔊 百度配置", 1)
            baidu_frame = tk.Frame(main_frame, bg='#2D2D2D')
            baidu_frame.pack(fill=tk.X, pady=(0, 15))

            self.create_input(baidu_frame, "API Key:", self.baidu_api_key_var, 0)
            self.create_input(baidu_frame, "Secret Key:", self.baidu_secret_key_var, 1)

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
            'baidu_api_key': self.baidu_api_key_var.get(),
            'baidu_secret_key': self.baidu_secret_key_var.get(),
            'api_key': self.llm_api_key_var.get(),
            'model': self.llm_model_var.get()
        }

        if settings['speech_api'] == "aliyun" and not settings['aliyun_appkey']:
            messagebox.showerror("错误", "请输入阿里云 AppKey！")
            return

        if settings['speech_api'] == "baidu" and (not settings['baidu_api_key'] or not settings['baidu_secret_key']):
            messagebox.showerror("错误", "请输入百度 API Key 和 Secret Key！")
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
