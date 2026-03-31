#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocabGo 翻译助手 - GUI版本
功能：语音识别 + 自动翻译，Translumo 风格界面
"""

import ctypes
import platform
import traceback
import tkinter as tk
import winreg

def set_dpi_awareness():
    """
    使程序识别 Windows 的高 DPI 缩放，解决截图偏移和模糊问题
    """
    try:
        # 仅针对 Windows 系统
        if platform.system() == "Windows":
            # 尝试使用新的 DPI 感知 API
            try:
                ctypes.windll.shcore.SetProcessDpiAwarenessContext(2)
                print("[INFO] 使用 SetProcessDpiAwarenessContext (Windows 10+)")
            except (AttributeError, OSError):
                # 回退到旧版 API
                try:
                    ctypes.windll.user32.SetProcessDpiAware(1)
                    print("[INFO] 使用 SetProcessDpiAware (Windows 7/8)")
                except Exception as e:
                    print(f"[WARNING] DPI感知设置完全失败: {e}")
        else:
            # 非Windows系统，不做处理
            pass
    except Exception as e:
        print(f"[WARNING] DPI感知设置失败: {e}")

# 在程序最开始执行，必须在任何GUI库导入之前
set_dpi_awareness()
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

# 导入OCR引擎
from ocr_engine_v2 import VocabGoOCR
from baidu_ocr import BaiduOCR

# ================= UI 主题配置 =================
THEME = {
    # 背景色
    "bg_dark":      "#0F1117",   # 最深背景
    "bg_mid":       "#1A1D27",   # 卡片背景
    "bg_light":     "#252836",   # 输入框背景
    "bg_bar":       "#13151E",   # 标题栏 / 底栏

    # 文字
    "fg_primary":   "#E8EAF0",   # 主文字
    "fg_secondary": "#6B7280",   # 次要文字
    "fg_accent_en": "#60A5FA",   # 英文标签（蓝）
    "fg_accent_zh": "#FBBF24",   # 中文标签（金）
    "fg_section":   "#A78BFA",   # 设置分区标题（紫）

    # 强调色
    "accent_blue":  "#3B82F6",
    "accent_green": "#10B981",
    "accent_red":   "#EF4444",
    "accent_gray":  "#4B5563",
    "accent_amber": "#F59E0B",
    "accent_purple":"#8B5CF6",

    # 字体
    "font_title":   ("Microsoft YaHei UI", 11, "bold"),
    "font_body":    ("Microsoft YaHei UI", 10),
    "font_small":   ("Microsoft YaHei UI", 9),
    "font_en_text": ("Consolas", 13),
    "font_zh_text": ("Microsoft YaHei UI", 13),
    "font_status":  ("Microsoft YaHei UI", 9),
    "font_label":   ("Microsoft YaHei UI", 10, "bold"),
    "font_section": ("Microsoft YaHei UI", 10, "bold"),
    "font_btn":     ("Microsoft YaHei UI", 9, "bold"),
}

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
    print("[FAILED] 配置文件加载失败")
    sys.exit(1)

# API 配置
LLM_API_URL = config.get("api_url", "")
LLM_API_KEY = config.get("api_key", "")
LLM_MODEL = config.get("model", "qwen-plus")

# 语音识别 API 选择
SPEECH_API = config.get("speech_api", "aliyun")
ALIYUN_APPKEY = config.get("aliyun_appkey", "")
ALIYUN_TOKEN = config.get("aliyun_token", "")

# 百度OCR API配置（用户提供的）
BAI_DU_OCR_API_KEY = config.get("baidu_ocr_api_key", "x8o9repM7KgO525AiyzeFGma")
BAI_DU_OCR_SECRET_KEY = config.get("baidu_ocr_secret_key", "i6hr5CVKwieQcnbVdwX8TqOHQYI8wPar")

# 旧版百度配置（保持兼容性）
BAI_DU_API_KEY = config.get("baidu_api_key", "")
BAI_DU_SECRET_KEY = config.get("baidu_secret_key", "")

# OCR配置
OCR_ENABLED = config.get("ocr_enabled", True)
OCR_HOTKEY = config.get("ocr_hotkey", "f8")
OCR_LANG = config.get("ocr_lang", "chi_sim+eng")
OCR_ENGINE = config.get("ocr_engine", "tesseract")  # "tesseract" 或 "baidu"
DPI_SCALE = config.get("dpi_scale", 1.0)  # DPI缩放因子

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
            return "[WARNING] API Key 未配置"

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
                return "[FAILED] 翻译失败"

            # 缓存结果
            self.cache[english_text.lower()] = translation
            return translation
        except Exception as e:
            print(f"翻译失败: {e}")
            return "❌ 翻译失败"

# ================= OCR 识别器（支持多引擎） =================
class OCRRecognizer:
    def __init__(self):
        self.ocr_engine = None
        self.baidu_ocr = None
        self.available = False
        self.engine_type = OCR_ENGINE  # "tesseract" 或 "baidu"

        # 初始化选定的OCR引擎
        self._initialize_engine()

    def _initialize_engine(self):
        """初始化选定的OCR引擎"""
        try:
            if self.engine_type == "tesseract":
                print("[INFO] 初始化Tesseract OCR引擎...")
                self.ocr_engine = VocabGoOCR()
                self.baidu_ocr = None
                self.available = True
                print("[SUCCESS] Tesseract OCR引擎初始化成功")

            elif self.engine_type == "baidu":
                if not BAI_DU_API_KEY or not BAI_DU_SECRET_KEY:
                    print("[WARNING] 百度OCR API Key未配置")
                    self.available = False
                    return

                print("[INFO] 初始化百度OCR引擎...")
                self.baidu_ocr = BaiduOCR(BAI_DU_API_KEY, BAI_DU_SECRET_KEY)
                self.ocr_engine = None
                self.available = True
                print("[SUCCESS] 百度OCR引擎初始化成功")

            else:
                print(f"[ERROR] 未知的OCR引擎类型: {self.engine_type}")
                self.available = False

        except Exception as e:
            print(f"[FAILED] OCR引擎初始化失败: {e}")
            self.available = False

    def is_available(self):
        """检查 OCR 是否可用"""
        return self.available and OCR_ENABLED

    def recognize_sync(self, image):
        """同步 OCR 识别"""
        if not self.available:
            return "[FAILED] OCR 引擎不可用"

        try:
            if self.engine_type == "tesseract":
                # 使用Tesseract引擎
                result = self.ocr_engine.recognize(image)
                if result and result.text:
                    return result.text
                else:
                    return "[FAILED] 未识别到文字"

            elif self.engine_type == "baidu":
                # 使用百度OCR引擎
                result = self.baidu_ocr.recognize(image)
                if result.get("success") and result.get("text"):
                    return result["text"]
                else:
                    error = result.get("error", "未知错误")
                    return f"[FAILED] 百度OCR: {error}"

            else:
                return "[FAILED] 未知的OCR引擎"

        except Exception as e:
            print(f"OCR 识别失败: {e}")
            return f"[FAILED] OCR 识别失败: {str(e)}"

# ================= OCR 区域选择窗口 =================
class OCRWindow:
    """类似 Translumo 的 OCR 窗口"""
    def __init__(self, parent, ocr_recognizer, translator, dpi_scale=1.0):
        self.parent = parent
        self.ocr_recognizer = ocr_recognizer
        self.translator = translator
        self.dpi_scale = dpi_scale  # 使用传入的DPI缩放因子

        # 实时翻译控制
        self.realtime_active = False
        self.realtime_thread = None
        self.stop_realtime = False

        print(f"[INFO] 使用DPI缩放因子: {self.dpi_scale}")

        # 创建全屏窗口
        self.window = tk.Toplevel(parent)
        self.window.title("VocabGo OCR")
        self.window.geometry("800x600+300+100")
        self.window.attributes('-topmost', True)
        self.window.configure(bg=THEME["bg_dark"])
        self.window.attributes('-alpha', 0.96)  # 稍微透明

        # 选择区域参数
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None
        self.is_selecting = False
        self.selected_coords = None  # (x1, y1, x2, y2)

        # 快捷键监听
        self.hotkey_registered = False
        self.window.bind("<Destroy>", self.on_destroy)
        self.ocr_hotkey = "~"  # 使用~键

        # 创建界面
        self.create_widgets()

        # 注册快捷键
        self.register_hotkey()

    def get_dpi_scale(self):
        """获取当前系统的DPI缩放因子（简化版）"""
        try:
            if platform.system() == "Windows":
                # 简单方法：直接从配置文件读取
                scale = config.get("dpi_scale", 1.0)
                print(f"[INFO] 从配置文件读取DPI缩放因子: {scale:.2f}")
                return scale
        except Exception as e:
            print(f"[WARNING] 获取DPI缩放失败: {e}")

        print("[INFO] 使用默认DPI缩放因子: 1.0")
        return 1.0

    def create_widgets(self):
        """创建界面组件"""
        T = THEME

        # ── 标题栏 ──────────────────────────────────
        title_frame = tk.Frame(self.window, bg=T["bg_bar"], height=36)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame, text="  OCR  ·  文字识别",
            bg=T["bg_bar"], fg=T["fg_primary"],
            font=T["font_title"]
        ).pack(side=tk.LEFT, padx=8)

        # ── 提示 ─────────────────────────────────────
        info_frame = tk.Frame(self.window, bg=T["bg_mid"], padx=12, pady=8)
        info_frame.pack(fill=tk.X, padx=10, pady=(8, 0))

        tk.Label(
            info_frame,
            text=f"① 点击「选区」拖选屏幕区域    ② 按 ~ 键启动/停止实时翻译    ③ 自动翻译",
            bg=T["bg_mid"], fg=T["fg_secondary"],
            font=T["font_small"], justify=tk.LEFT
        ).pack(anchor=tk.W)

        # ── 主内容区域 ────────────────────────────────
        main_frame = tk.Frame(self.window, bg=T["bg_dark"], padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 英文区
        en_hdr = tk.Frame(main_frame, bg=T["bg_dark"])
        en_hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(en_hdr, text="EN", bg=T["bg_dark"],
                 fg=T["fg_accent_en"], font=T["font_label"]).pack(side=tk.LEFT)
        tk.Label(en_hdr, text=" 识别文字", bg=T["bg_dark"],
                 fg=T["fg_secondary"], font=T["font_small"]).pack(side=tk.LEFT)

        self.english_text = scrolledtext.ScrolledText(
            main_frame, height=6,
            bg=T["bg_mid"], fg=T["fg_primary"],
            font=T["font_en_text"], wrap=tk.WORD,
            relief=tk.FLAT, insertbackground=T["fg_primary"],
            padx=8, pady=6
        )
        self.english_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 分隔线
        tk.Frame(main_frame, bg=T["bg_light"], height=1).pack(fill=tk.X, pady=(0, 8))

        # 中文区
        zh_hdr = tk.Frame(main_frame, bg=T["bg_dark"])
        zh_hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(zh_hdr, text="ZH", bg=T["bg_dark"],
                 fg=T["fg_accent_zh"], font=T["font_label"]).pack(side=tk.LEFT)
        tk.Label(zh_hdr, text=" 中文翻译", bg=T["bg_dark"],
                 fg=T["fg_secondary"], font=T["font_small"]).pack(side=tk.LEFT)

        self.chinese_text = scrolledtext.ScrolledText(
            main_frame, height=4,
            bg=T["bg_mid"], fg=T["fg_primary"],
            font=T["font_zh_text"], wrap=tk.WORD,
            relief=tk.FLAT, insertbackground=T["fg_primary"],
            padx=8, pady=6
        )
        self.chinese_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 状态
        status_frame = tk.Frame(main_frame, bg=T["bg_dark"])
        status_frame.pack(fill=tk.X)
        self.status_label = tk.Label(
            status_frame, text="● 等待选择区域...",
            bg=T["bg_dark"], fg=T["fg_secondary"],
            font=T["font_status"]
        )
        self.status_label.pack(side=tk.LEFT)

        # ── 底部工具栏 ────────────────────────────────
        button_frame = tk.Frame(self.window, bg=T["bg_bar"], height=44)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)

        inner = tk.Frame(button_frame, bg=T["bg_bar"])
        inner.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

        def _btn(text, bg, cmd):
            return tk.Button(
                inner, text=text, bg=bg, fg=T["fg_primary"],
                font=T["font_btn"], relief=tk.FLAT,
                activebackground=bg, activeforeground=T["fg_primary"],
                bd=0, padx=10, pady=4, cursor="hand2", command=cmd
            )

        _btn("选区", T["accent_green"], self.start_selection).pack(side=tk.LEFT, padx=(0, 4))
        _btn("清空", T["accent_gray"], self.clear_text).pack(side=tk.LEFT, padx=(0, 4))

        # 实时翻译按钮
        self.realtime_btn = _btn("实时翻译", T["accent_blue"], self.toggle_realtime)
        self.realtime_btn.pack(side=tk.LEFT, padx=(0, 4))

        _btn("关闭", T["accent_red"], self.close).pack(side=tk.LEFT)

        tk.Label(
            button_frame,
            text=f"  快捷键  ~",
            bg=T["bg_bar"], fg=T["fg_secondary"],
            font=T["font_small"]
        ).pack(side=tk.RIGHT, padx=10)

    def register_hotkey(self):
        """注册快捷键"""
        try:
            keyboard.add_hotkey(self.ocr_hotkey, self.toggle_realtime)
            self.hotkey_registered = True
            print(f"[SUCCESS] 快捷键 `~` 已注册")
        except Exception as e:
            print(f"[WARNING] 快捷键注册失败: {e}")
            self.hotkey_registered = False

    def on_destroy(self, event):
        """窗口销毁时清理"""
        # 停止实时翻译
        self.stop_realtime_translation()

        if self.hotkey_registered:
            try:
                keyboard.remove_hotkey(self.ocr_hotkey)
                print("[SUCCESS] 快捷键已注销")
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
            self.status_label.config(text=f"📐 已选择区域 ({area_size})，按 ~ 键启动实时翻译")

    def cancel_selection(self, event):
        """取消选择"""
        self.is_selecting = False
        self.selected_coords = None
        self.selection_window.destroy()
        self.window.state('normal')
        self.window.deiconify()
        self.status_label.config(text="🟢 已取消，重新选择")

    def toggle_realtime(self):
        """切换实时翻译"""
        if not self.selected_coords:
            self.status_label.config(text="[WARNING] 请先选择区域")
            return

        if self.realtime_active:
            # 停止实时翻译
            self.stop_realtime_translation()
        else:
            # 启动实时翻译
            self.start_realtime_translation()

    def start_realtime_translation(self):
        """启动实时翻译"""
        self.realtime_active = True
        self.stop_realtime = False
        self.status_label.config(text="🔄 实时翻译中...")
        self.realtime_btn.config(text="停止翻译", bg=T["accent_red"])

        # 启动实时翻译线程
        self.realtime_thread = threading.Thread(target=self.realtime_translation_loop, daemon=True)
        self.realtime_thread.start()

        print("[INFO] 实时翻译已启动")

    def stop_realtime_translation(self):
        """停止实时翻译"""
        if self.realtime_active:
            self.realtime_active = False
            self.stop_realtime = True
            self.status_label.config(text="⏸️ 实时翻译已停止")
            self.realtime_btn.config(text="实时翻译", bg=T["accent_blue"])
            print("[INFO] 实时翻译已停止")

    def realtime_translation_loop(self):
        """实时翻译循环"""
        try:
            if not self.ocr_recognizer.is_available():
                self.window.after(0, lambda: self.status_label.config(text="[FAILED] OCR 不可用"))
                self.stop_realtime = True
                self.realtime_active = False
                return

            last_text = ""

            while not self.stop_realtime:
                # 执行OCR识别
                text = self.perform_single_ocr()

                if text and text != last_text and not text.startswith("[FAILED]"):
                    last_text = text

                    # 翻译
                    first_line = text.split('\n')[0].strip()
                    if first_line:
                        chinese = self.translator.translate(first_line)

                        # 更新界面
                        self.window.after(0, lambda t=text, c=chinese: self.update_display(t, c))
                        self.window.after(0, lambda: self.status_label.config(text="🔄 实时翻译中..."))

                # 间隔0.5秒再识别一次，避免过于频繁
                time.sleep(0.5)

        except Exception as e:
            print(f"[ERROR] 实时翻译循环异常: {e}")
            self.window.after(0, lambda: self.status_label.config(text=f"[FAILED] 错误: {str(e)[:30]}"))
            self.stop_realtime = True
            self.realtime_active = False

    def perform_single_ocr(self):
        """执行单次OCR识别"""
        try:
            # 直接截取选择区域
            x1, y1, x2, y2 = self.selected_coords

            # 根据DPI缩放因子调整坐标
            scaled_x1 = int(x1 * self.dpi_scale)
            scaled_y1 = int(y1 * self.dpi_scale)
            scaled_x2 = int(x2 * self.dpi_scale)
            scaled_y2 = int(y2 * self.dpi_scale)

            cropped = ImageGrab.grab(bbox=(scaled_x1, scaled_y1, scaled_x2, scaled_y2))

            # 执行 OCR
            extracted_text = self.ocr_recognizer.recognize_sync(cropped)
            return extracted_text

        except Exception as e:
            print(f"[ERROR] OCR识别异常: {e}")
            return f"[FAILED] {str(e)}"

    def update_display(self, english_text, chinese_text):
        """更新显示内容"""
        self.english_text.delete(1.0, tk.END)
        self.english_text.insert(tk.END, english_text)

        self.chinese_text.delete(1.0, tk.END)
        self.chinese_text.insert(tk.END, chinese_text)

    def clear_text(self):
        """清空文本"""
        self.english_text.delete(1.0, tk.END)
        self.chinese_text.delete(1.0, tk.END)

    def close(self):
        """关闭窗口"""
        if self.hotkey_registered:
            try:
                keyboard.remove_hotkey(self.ocr_hotkey)
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
        self.root.geometry("500x460+100+100")
        self.root.configure(bg=THEME["bg_dark"])

        # 可拖拽
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.do_move)

        # 初始化组件
        self.recorder = AudioRecorder()
        self.recognizer = SpeechRecognizer()
        self.translator = Translator()
        self.ocr_recognizer = OCRRecognizer()

        # OCR 窗口
        self.ocr_window = None

        # 创建界面
        self.create_widgets()

        # 自动启动录音
        self.start_listening()

    def _make_btn(self, parent, text, bg, command, width=None):
        """统一按钮样式工厂"""
        kw = dict(
            text=text, bg=bg, fg=THEME["fg_primary"],
            font=THEME["font_btn"], relief=tk.FLAT,
            activebackground=bg, activeforeground=THEME["fg_primary"],
            bd=0, padx=10, pady=4,
            cursor="hand2", command=command
        )
        if width:
            kw["width"] = width
        return tk.Button(parent, **kw)

    def create_widgets(self):
        """创建界面组件"""
        T = THEME

        # ── 标题栏 ──────────────────────────────────────
        title_frame = tk.Frame(self.root, bg=T["bg_bar"], height=36)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        api_name = "阿里云" if SPEECH_API == "aliyun" else "百度"
        tk.Label(
            title_frame,
            text=f"  VocabGo  ·  语音翻译  ({api_name})",
            bg=T["bg_bar"], fg=T["fg_primary"],
            font=T["font_title"]
        ).pack(side=tk.LEFT, padx=8, pady=0)

        # ── 主内容区域 ──────────────────────────────────
        main_frame = tk.Frame(self.root, bg=T["bg_dark"], padx=12, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 英文识别区
        en_header = tk.Frame(main_frame, bg=T["bg_dark"])
        en_header.pack(fill=tk.X, pady=(0, 4))
        tk.Label(en_header, text="EN", bg=T["bg_dark"],
                 fg=T["fg_accent_en"], font=T["font_label"]).pack(side=tk.LEFT)
        tk.Label(en_header, text=" 英文识别", bg=T["bg_dark"],
                 fg=T["fg_secondary"], font=T["font_small"]).pack(side=tk.LEFT)

        self.english_text = scrolledtext.ScrolledText(
            main_frame, height=5,
            bg=T["bg_mid"], fg=T["fg_primary"],
            font=T["font_en_text"], wrap=tk.WORD,
            relief=tk.FLAT, insertbackground=T["fg_primary"],
            selectbackground=T["accent_blue"],
            padx=8, pady=6
        )
        self.english_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 分隔线
        tk.Frame(main_frame, bg=T["bg_light"], height=1).pack(fill=tk.X, pady=(0, 10))

        # 中文翻译区
        zh_header = tk.Frame(main_frame, bg=T["bg_dark"])
        zh_header.pack(fill=tk.X, pady=(0, 4))
        tk.Label(zh_header, text="ZH", bg=T["bg_dark"],
                 fg=T["fg_accent_zh"], font=T["font_label"]).pack(side=tk.LEFT)
        tk.Label(zh_header, text=" 中文翻译", bg=T["bg_dark"],
                 fg=T["fg_secondary"], font=T["font_small"]).pack(side=tk.LEFT)

        self.chinese_text = scrolledtext.ScrolledText(
            main_frame, height=5,
            bg=T["bg_mid"], fg=T["fg_primary"],
            font=T["font_zh_text"], wrap=tk.WORD,
            relief=tk.FLAT, insertbackground=T["fg_primary"],
            selectbackground=T["accent_blue"],
            padx=8, pady=6
        )
        self.chinese_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 状态栏（嵌在 main_frame 底部）
        status_frame = tk.Frame(main_frame, bg=T["bg_dark"])
        status_frame.pack(fill=tk.X)
        self.status_label = tk.Label(
            status_frame, text="● 等待音频...",
            bg=T["bg_dark"], fg=T["fg_secondary"],
            font=T["font_status"]
        )
        self.status_label.pack(side=tk.LEFT)

        # ── 底部工具栏 ──────────────────────────────────
        button_frame = tk.Frame(self.root, bg=T["bg_bar"], height=44)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)

        inner = tk.Frame(button_frame, bg=T["bg_bar"])
        inner.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

        self.pause_button = self._make_btn(inner, "⏸  暂停", T["accent_red"], self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=(0, 4))

        self._make_btn(inner, "清空", T["accent_gray"], self.clear_text).pack(side=tk.LEFT, padx=(0, 4))
        self._make_btn(inner, "⚙  设置", T["accent_purple"], self.open_settings).pack(side=tk.LEFT, padx=(0, 4))
        self._make_btn(inner, "OCR", T["accent_amber"], self.open_ocr_window).pack(side=tk.LEFT)

        # 右侧：透明度 + 置顶
        right = tk.Frame(button_frame, bg=T["bg_bar"])
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=6)

        self.topmost_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            right, text="置顶", variable=self.topmost_var,
            command=self.toggle_topmost,
            bg=T["bg_bar"], fg=T["fg_secondary"],
            selectcolor=T["accent_green"],
            activebackground=T["bg_bar"],
            font=T["font_small"]
        ).pack(side=tk.RIGHT, padx=(6, 0))

        tk.Label(right, text="透明", bg=T["bg_bar"],
                 fg=T["fg_secondary"], font=T["font_small"]).pack(side=tk.LEFT)

        self.opacity_scale = tk.Scale(
            right, from_=40, to=100, orient=tk.HORIZONTAL,
            bg=T["bg_bar"], fg=T["fg_secondary"],
            troughcolor=T["bg_mid"], highlightthickness=0,
            length=80, showvalue=False,
            command=self.update_opacity
        )
        self.opacity_scale.set(90)
        self.opacity_scale.pack(side=tk.LEFT, padx=4)

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
                self.pause_button.config(text="▶  继续", bg=THEME["accent_green"])
                self.update_status("● 已暂停")
            else:
                self.pause_button.config(text="⏸  暂停", bg=THEME["accent_red"])
                self.update_status("● 继续监听...")
        else:
            self.is_paused = False
            self.pause_button.config(text="⏸  暂停", bg=THEME["accent_red"])

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

                            self.update_status("[SUCCESS] 识别完成")
                        else:
                            self.update_status("[FAILED] 识别失败")

                    time.sleep(0.5)

                except Exception as e:
                    self.update_status(f"[ERROR] 错误: {str(e)[:30]}")
                    time.sleep(1)

        threading.Thread(target=listen_loop, daemon=True).start()

    def open_settings(self):
        """打开设置窗口"""
        SettingsWindow(self.root, self.apply_settings)

    def open_ocr_window(self):
        """打开 OCR 窗口"""
        if self.ocr_window is None or not self.ocr_window.window.winfo_exists():
            # 获取DPI缩放因子
            dpi_scale = config.get("dpi_scale", 1.0)
            self.ocr_window = OCRWindow(self.root, self.ocr_recognizer, self.translator, dpi_scale)

    def apply_settings(self, settings):
        """应用设置"""
        global SPEECH_API, ALIYUN_APPKEY, ALIYUN_TOKEN, LLM_API_KEY, LLM_MODEL
        global OCR_ENABLED, OCR_HOTKEY, OCR_LANG, DPI_SCALE
        global config

        SPEECH_API = settings.get('speech_api', 'aliyun')
        ALIYUN_APPKEY = settings.get('aliyun_appkey', '')
        ALIYUN_TOKEN = settings.get('aliyun_token', '')
        LLM_API_KEY = settings.get('api_key', '')
        LLM_MODEL = settings.get('model', 'qwen-plus')

        OCR_ENABLED = settings.get('ocr_enabled', True)
        OCR_HOTKEY = settings.get('ocr_hotkey', 'f8')
        OCR_LANG = settings.get('ocr_lang', 'chi_sim+eng')
        DPI_SCALE = settings.get('dpi_scale', 1.0)
        OCR_ENGINE = settings.get('ocr_engine', 'tesseract')

        config['speech_api'] = SPEECH_API
        config['aliyun_appkey'] = ALIYUN_APPKEY
        config['aliyun_token'] = ALIYUN_TOKEN
        config['api_key'] = LLM_API_KEY
        config['model'] = LLM_MODEL
        config['ocr_enabled'] = OCR_ENABLED
        config['ocr_hotkey'] = OCR_HOTKEY
        config['ocr_lang'] = OCR_LANG
        config['dpi_scale'] = settings.get('dpi_scale', 1.0)

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        api_name = "阿里云" if SPEECH_API == "aliyun" else "百度"
        self.root.title(f"VocabGo 翻译助手 ({api_name})")
        self.translator.cache = {}

        # 更新OCR识别器（考虑引擎切换）
        self.ocr_recognizer = OCRRecognizer()

        # 根据OCR引擎类型显示不同消息
        if self.ocr_recognizer.engine_type == "tesseract":
            ocr_msg = "Tesseract OCR引擎"
        elif self.ocr_recognizer.engine_type == "baidu":
            ocr_msg = "百度OCR引擎"
        else:
            ocr_msg = "未知OCR引擎"

        messagebox.showinfo("设置", f"设置已保存！\n当前OCR引擎: {ocr_msg}\n部分设置需要重启应用生效。")

class SettingsWindow:
    def __init__(self, parent, apply_callback):
        self.parent = parent
        self.apply_callback = apply_callback

        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("500x620+200+100")
        self.window.configure(bg=THEME["bg_dark"])
        self.window.transient(parent)
        self.window.grab_set()

        self.speech_api_var = tk.StringVar(value=SPEECH_API)
        self.aliyun_appkey_var = tk.StringVar(value=ALIYUN_APPKEY)
        self.aliyun_token_var = tk.StringVar(value=ALIYUN_TOKEN)
        self.baidu_api_key_var = tk.StringVar(value=BAI_DU_API_KEY)
        self.baidu_secret_key_var = tk.StringVar(value=BAI_DU_SECRET_KEY)
        self.baidu_ocr_api_key_var = tk.StringVar(value=BAI_DU_OCR_API_KEY)
        self.baidu_ocr_secret_key_var = tk.StringVar(value=BAI_DU_OCR_SECRET_KEY)
        self.llm_api_key_var = tk.StringVar(value=LLM_API_KEY)
        self.llm_model_var = tk.StringVar(value=LLM_MODEL)

        # OCR配置变量
        self.ocr_enabled_var = tk.BooleanVar(value=OCR_ENABLED)
        self.ocr_hotkey_var = tk.StringVar(value=OCR_HOTKEY)
        self.ocr_lang_var = tk.StringVar(value=OCR_LANG)
        self.ocr_engine_var = tk.StringVar(value=OCR_ENGINE)
        self.dpi_scale_var = tk.StringVar(value=str(config.get("dpi_scale", "1.0")))

        self.create_widgets()

    def create_widgets(self):
        T = THEME

        # 标题栏
        title_frame = tk.Frame(self.window, bg=T["bg_bar"], height=36)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame, text="  ⚙  VocabGo  ·  设置",
            bg=T["bg_bar"], fg=T["fg_primary"],
            font=T["font_title"]
        ).pack(side=tk.LEFT, padx=8)

        # 可滚动主框架
        canvas = tk.Canvas(self.window, bg=T["bg_dark"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.window, orient="vertical", command=canvas.yview,
                                  bg=T["bg_mid"], troughcolor=T["bg_dark"])
        main_frame = tk.Frame(canvas, bg=T["bg_dark"], padx=15, pady=10)

        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=main_frame, anchor="nw", width=500)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # OCR设置区域
        self.create_section(main_frame, "📷  OCR 功能", 0)
        ocr_frame = tk.Frame(main_frame, bg=THEME["bg_dark"])
        ocr_frame.pack(fill=tk.X, pady=(0, 15))

        # OCR引擎选择
        ocr_engine_frame = tk.Frame(ocr_frame, bg=THEME["bg_dark"])
        ocr_engine_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            ocr_engine_frame, text="引擎:",
            bg=THEME["bg_dark"], fg=THEME["fg_primary"],
            font=THEME["font_body"]
        ).pack(side=tk.LEFT)

        # OCR引擎选择变量
        self.ocr_engine_var = tk.StringVar(value=OCR_ENGINE)
        ocr_engine_choices = ["tesseract", "baidu"]

        def _radio(parent, text, val, cmd):
            return tk.Radiobutton(
                parent, text=text, variable=self.ocr_engine_var, value=val,
                bg=THEME["bg_dark"], fg=THEME["fg_primary"],
                selectcolor=THEME["accent_green"],
                activebackground=THEME["bg_dark"],
                font=THEME["font_small"], command=cmd
            )

        _radio(ocr_engine_frame, "Tesseract（本地）", "tesseract",
               self.toggle_ocr_engine).pack(side=tk.LEFT, padx=(10, 0))
        _radio(ocr_engine_frame, "百度OCR（云端）", "baidu",
               self.toggle_ocr_engine).pack(side=tk.LEFT, padx=(10, 0))

        # 启用OCR
        tk.Checkbutton(
            ocr_frame, text="启用 OCR 功能",
            variable=self.ocr_enabled_var,
            bg=THEME["bg_dark"], fg=THEME["fg_primary"],
            selectcolor=THEME["accent_green"],
            activebackground=THEME["bg_dark"],
            font=THEME["font_body"]
        ).pack(anchor=tk.W)

        # OCR快捷键
        ocr_hotkey_frame = tk.Frame(ocr_frame, bg=THEME["bg_dark"])
        ocr_hotkey_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(
            ocr_hotkey_frame, text="快捷键:",
            bg=THEME["bg_dark"], fg=THEME["fg_primary"],
            font=THEME["font_small"]
        ).pack(side=tk.LEFT)

        tk.Entry(
            ocr_hotkey_frame, textvariable=self.ocr_hotkey_var,
            bg=THEME["bg_mid"], fg=THEME["fg_primary"],
            font=THEME["font_body"], relief=tk.FLAT,
            insertbackground=THEME["fg_primary"], width=15
        ).pack(side=tk.LEFT, padx=(10, 0))

        # OCR语言
        ocr_lang_frame = tk.Frame(ocr_frame, bg=THEME["bg_dark"])
        ocr_lang_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(
            ocr_lang_frame, text="识别语言:",
            bg=THEME["bg_dark"], fg=THEME["fg_primary"],
            font=THEME["font_small"]
        ).pack(side=tk.LEFT)

        ocr_lang_choices = ["chi_sim+eng", "eng", "chi_sim"]
        ocr_lang_combo = ttk.Combobox(
            ocr_lang_frame, values=ocr_lang_choices,
            textvariable=self.ocr_lang_var,
            state="readonly", width=15
        )
        ocr_lang_combo.pack(side=tk.LEFT, padx=(10, 0))

        # DPI缩放因子
        dpi_scale_frame = tk.Frame(ocr_frame, bg=THEME["bg_dark"])
        dpi_scale_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(
            dpi_scale_frame, text="DPI缩放:",
            bg=THEME["bg_dark"], fg=THEME["fg_primary"],
            font=THEME["font_small"]
        ).pack(side=tk.LEFT)

        dpi_scale_entry = tk.Entry(
            dpi_scale_frame, bg=THEME["bg_mid"], fg=THEME["fg_primary"],
            font=THEME["font_body"], relief=tk.FLAT,
            insertbackground=THEME["fg_primary"],
            width=8, textvariable=self.dpi_scale_var
        )
        dpi_scale_entry.pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(
            dpi_scale_frame, text="(100%→1.0  125%→1.25  150%→1.5)",
            bg=THEME["bg_dark"], fg=THEME["fg_secondary"],
            font=THEME["font_small"]
        ).pack(side=tk.LEFT, padx=5)

        # 百度OCR API配置区域（初始隐藏）
        self.baidu_ocr_config_frame = tk.Frame(ocr_frame, bg=THEME["bg_dark"])

        tk.Label(
            self.baidu_ocr_config_frame, text="百度OCR API 配置",
            bg=THEME["bg_dark"], fg=THEME["fg_section"],
            font=THEME["font_section"]
        ).pack(anchor=tk.W, pady=(15, 5))

        self.create_input(self.baidu_ocr_config_frame, "OCR API Key:", self.baidu_ocr_api_key_var, 0)
        self.create_input(self.baidu_ocr_config_frame, "OCR Secret Key:", self.baidu_ocr_secret_key_var, 1)

        # 语音识别API设置
        self.create_section(main_frame, "🎤  语音识别 API", 1)
        api_frame = tk.Frame(main_frame, bg=THEME["bg_dark"])
        api_frame.pack(fill=tk.X, pady=(0, 15))

        def _rapi(text, val):
            return tk.Radiobutton(
                api_frame, text=text, variable=self.speech_api_var, value=val,
                bg=THEME["bg_dark"], fg=THEME["fg_primary"],
                selectcolor=THEME["accent_green"],
                activebackground=THEME["bg_dark"],
                font=THEME["font_body"],
                command=self.toggle_speech_api
            )

        _rapi("阿里云语音识别", "aliyun").pack(anchor=tk.W)
        _rapi("百度语音识别", "baidu").pack(anchor=tk.W, pady=(5, 0))

        # 阿里云配置区域（动态切换）
        self.aliyun_section_label = tk.Label(main_frame, text="☁  阿里云配置",
                                              bg=THEME["bg_dark"], fg=THEME["fg_section"],
                                              font=THEME["font_section"])
        self.aliyun_config_frame = tk.Frame(main_frame, bg=THEME["bg_dark"])
        self.create_input(self.aliyun_config_frame, "AppKey:", self.aliyun_appkey_var, 0)
        self.create_input(self.aliyun_config_frame, "Token (可选，留空自动获取):", self.aliyun_token_var, 1)

        # 百度语音识别配置区域（动态切换）
        self.baidu_section_label = tk.Label(main_frame, text="🔊  百度配置",
                                             bg=THEME["bg_dark"], fg=THEME["fg_section"],
                                             font=THEME["font_section"])
        self.baidu_config_frame = tk.Frame(main_frame, bg=THEME["bg_dark"])
        self.create_input(self.baidu_config_frame, "API Key:", self.baidu_api_key_var, 0)
        self.create_input(self.baidu_config_frame, "Secret Key:", self.baidu_secret_key_var, 1)

        # 初始化显示对应的配置区域
        if SPEECH_API == "aliyun":
            self.show_aliyun_config()
        else:
            self.show_baidu_config()

        # 初始化OCR引擎显示
        self.toggle_ocr_engine()

        self.create_section(main_frame, "🧠  通义千问配置", 3)
        llm_frame = tk.Frame(main_frame, bg=THEME["bg_dark"])
        llm_frame.pack(fill=tk.X, pady=(0, 15))

        self.create_input(llm_frame, "API Key:", self.llm_api_key_var, 0)

        model_frame = tk.Frame(llm_frame, bg=THEME["bg_dark"])
        model_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(
            model_frame, text="模型:", bg=THEME["bg_dark"],
            fg=THEME["fg_primary"], font=THEME["font_small"]
        ).pack(side=tk.LEFT)

        models = ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"]
        self.model_combobox = ttk.Combobox(
            model_frame, values=models, textvariable=self.llm_model_var,
            state="readonly", width=15
        )
        self.model_combobox.pack(side=tk.LEFT, padx=(10, 0))

        # 创建按钮（固定在底部）
        self.create_buttons()

    def create_buttons(self):
        """创建保存和取消按钮（固定在底部）"""
        T = THEME
        button_frame = tk.Frame(self.window, bg=T["bg_bar"], height=50)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)

        def _btn(text, bg, cmd):
            return tk.Button(
                button_frame, text=text, bg=bg, fg=T["fg_primary"],
                font=T["font_btn"], relief=tk.FLAT,
                activebackground=bg, activeforeground=T["fg_primary"],
                bd=0, padx=14, pady=6, cursor="hand2", command=cmd
            )

        _btn("✓  保存", T["accent_green"], self.save_settings).pack(side=tk.LEFT, padx=12, pady=10)
        _btn("✕  取消", T["accent_red"], self.window.destroy).pack(side=tk.LEFT, padx=0, pady=10)

    def create_section(self, parent, title, section_num):
        T = THEME
        section_frame = tk.Frame(parent, bg=T["bg_dark"])
        section_frame.pack(fill=tk.X, pady=(10 if section_num == 0 else 18, 0))

        # 左色块装饰
        tk.Frame(section_frame, bg=T["accent_purple"], width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        tk.Label(
            section_frame, text=title,
            bg=T["bg_dark"], fg=T["fg_section"],
            font=T["font_section"]
        ).pack(anchor=tk.W, side=tk.LEFT)

    def create_input(self, parent, label, variable, padx):
        T = THEME
        input_frame = tk.Frame(parent, bg=T["bg_dark"])
        input_frame.pack(fill=tk.X, pady=(10 if padx == 0 else 5, 0), padx=padx)

        tk.Label(
            input_frame, text=label,
            bg=T["bg_dark"], fg=T["fg_secondary"],
            font=T["font_small"], width=22, anchor=tk.W
        ).pack(side=tk.LEFT)

        entry = tk.Entry(
            input_frame, textvariable=variable,
            bg=T["bg_mid"], fg=T["fg_primary"],
            font=T["font_body"], relief=tk.FLAT,
            insertbackground=T["fg_primary"],
            show='*' if ('Key' in label or 'Token' in label) else ''
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0), ipady=3)

    def toggle_ocr_engine(self):
        """切换OCR引擎时动态显示/隐藏配置"""
        if self.ocr_engine_var.get() == "baidu":
            self.baidu_ocr_config_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.baidu_ocr_config_frame.pack_forget()

    def toggle_speech_api(self):
        """切换语音API时动态显示对应配置"""
        if self.speech_api_var.get() == "aliyun":
            self.show_aliyun_config()
        else:
            self.show_baidu_config()

    def show_aliyun_config(self):
        """显示阿里云配置"""
        self.aliyun_section_label.pack(anchor=tk.W, pady=(15, 0))
        self.aliyun_config_frame.pack(fill=tk.X, pady=(0, 15))
        self.baidu_section_label.pack_forget()
        self.baidu_config_frame.pack_forget()

    def show_baidu_config(self):
        """显示百度配置"""
        self.baidu_section_label.pack(anchor=tk.W, pady=(15, 0))
        self.baidu_config_frame.pack(fill=tk.X, pady=(0, 15))
        self.aliyun_section_label.pack_forget()
        self.aliyun_config_frame.pack_forget()

    def save_settings(self):
        settings = {
            'speech_api': self.speech_api_var.get(),
            'aliyun_appkey': self.aliyun_appkey_var.get(),
            'aliyun_token': self.aliyun_token_var.get(),
            'baidu_api_key': self.baidu_api_key_var.get(),
            'baidu_secret_key': self.baidu_secret_key_var.get(),
            'baidu_ocr_api_key': self.baidu_ocr_api_key_var.get(),
            'baidu_ocr_secret_key': self.baidu_ocr_secret_key_var.get(),
            'api_key': self.llm_api_key_var.get(),
            'model': self.llm_model_var.get(),
            'ocr_enabled': self.ocr_enabled_var.get(),
            'ocr_hotkey': self.ocr_hotkey_var.get().lower(),
            'ocr_lang': self.ocr_lang_var.get(),
            'ocr_engine': self.ocr_engine_var.get(),
            'dpi_scale': float(self.dpi_scale_var.get())
        }

        if settings['speech_api'] == "aliyun" and not settings['aliyun_appkey']:
            messagebox.showerror("错误", "请输入阿里云 AppKey！")
            return

        if settings['speech_api'] == "baidu" and (not settings['baidu_api_key'] or not settings['baidu_secret_key']):
            messagebox.showerror("错误", "请输入百度 API Key 和 Secret Key！")
            return

        # 百度OCR API Key验证
        if settings['ocr_engine'] == "baidu" and (not settings['baidu_ocr_api_key'] or not settings['baidu_ocr_secret_key']):
            messagebox.showerror("错误", "百度OCR需要配置API Key和Secret Key！")
            return

        if not settings['api_key']:
            messagebox.showerror("错误", "请输入通义千问 API Key！")
            return

        self.apply_callback(settings)
        self.window.destroy()

# ================= 主函数 =================
def main():
    root = tk.Tk()

    # ── ttk 深色主题（Combobox / Scrollbar） ──
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TCombobox",
        fieldbackground=THEME["bg_mid"],
        background=THEME["bg_mid"],
        foreground=THEME["fg_primary"],
        selectbackground=THEME["accent_blue"],
        selectforeground=THEME["fg_primary"],
        bordercolor=THEME["bg_light"],
        arrowcolor=THEME["fg_secondary"],
        padding=4
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", THEME["bg_mid"])],
        foreground=[("readonly", THEME["fg_primary"])]
    )
    style.configure("TScrollbar",
        background=THEME["bg_mid"],
        troughcolor=THEME["bg_dark"],
        bordercolor=THEME["bg_dark"],
        arrowcolor=THEME["fg_secondary"]
    )

    app = TranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
