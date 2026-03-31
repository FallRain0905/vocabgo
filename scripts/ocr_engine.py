#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows原生OCR引擎
使用Windows Runtime OCR API，轻量级、高性能、离线可用
支持中文和英文识别，提供精确的文本坐标信息
"""

import asyncio
from PIL import Image
import mss

# 尝试导入Windows OCR相关模块
WINSDK_AVAILABLE = False
try:
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.globalization import Language
    from winsdk.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat, BitmapAlphaMode
    from winsdk.windows.security.cryptography import CryptographicBuffer
    WINSDK_AVAILABLE = True
except ImportError:
    print("WARNING: winsdk not installed, Windows native OCR not available")
    print("   Install method: pip install winsdk (requires Visual Studio)")
    print("   Or use alternative OCR solutions")

import numpy as np


class WindowsOCR:
    """
    Windows原生OCR引擎
    利用Windows 10/11自带的OCR能力，无需额外安装模型
    """

    def __init__(self, lang_code="zh-Hans-CN"):
        """
        初始化Windows OCR引擎

        Args:
            lang_code: 语言代码
                      - 中文简体: "zh-Hans-CN"
                      - 英文: "en-US"
        """
        if not WINSDK_AVAILABLE:
            raise RuntimeError("winsdk模块未安装，无法使用Windows原生OCR")

        self.language = Language(lang_code)

        # 检查语言支持
        if not OcrEngine.is_language_supported(self.language):
            raise RuntimeError(f"系统未安装/不支持该语言的OCR: {lang_code}")

        # 创建OCR引擎实例
        self.engine = OcrEngine.try_create_from_language(self.language)
        if not self.engine:
            raise RuntimeError(f"无法创建OCR引擎，请检查系统语言包是否安装完整")

    async def _recognize_async(self, pil_image):
        """
        异步调用WinRT OCR识别

        Args:
            pil_image: PIL图像对象

        Returns:
            识别结果列表，每个元素包含文本和坐标信息
        """
        # 将PIL Image转换为RGBA格式（Windows OCR要求）
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")

        # 将图像数据转换为Windows运行时可接受的Buffer
        image_bytes = pil_image.tobytes()
        buffer = CryptographicBuffer.create_from_byte_array(image_bytes)

        # 创建SoftwareBitmap
        bitmap = SoftwareBitmap.create_copy_from_buffer(
            buffer,
            BitmapPixelFormat.RGBA8,
            pil_image.width,
            pil_image.height,
            BitmapAlphaMode.PREMULTIPLIED
        )

        # 执行OCR识别
        result = await self.engine.recognize_async(bitmap)

        # 提取文本和坐标信息
        extracted_data = []
        for line in result.lines:
            line_text = line.text
            # 获取整行的边界框坐标，可用于模拟点击
            rect = line.bounding_rect
            extracted_data.append({
                "text": line_text,
                "x": rect.x,
                "y": rect.y,
                "width": rect.width,
                "height": rect.height
            })

        return extracted_data

    def recognize(self, pil_image):
        """
        同步接口供外部调用

        Args:
            pil_image: PIL图像对象

        Returns:
            识别结果列表，每个元素包含文本和坐标信息
        """
        try:
            return asyncio.run(self._recognize_async(pil_image))
        except Exception as e:
            print(f"OCR识别失败: {e}")
            return []

    def recognize_text_only(self, pil_image):
        """
        仅提取文本，不包含坐标信息（简化版本）

        Args:
            pil_image: PIL图像对象

        Returns:
            识别出的纯文本字符串
        """
        results = self.recognize(pil_image)
        if results:
            return "\n".join([item["text"] for item in results])
        return ""


class OnlineOCREngine:
    """
    在线OCR引擎（备用方案）
    当Windows原生OCR不可用时使用
    """

    def __init__(self, api_key=None):
        """
        初始化在线OCR引擎

        Args:
            api_key: OCR服务API密钥
        """
        self.api_key = api_key
        print("WARNING: Using online OCR service (backup solution)")

    def recognize_text_only(self, pil_image):
        """
        在线OCR识别（简化版本）
        注意：这需要额外的API配置
        """
        # 这里可以集成百度OCR、腾讯OCR或其他在线OCR服务
        # 由于需要具体的API配置，这里只返回示例
        print("WARNING: Online OCR requires API configuration")
        return ""


# Tesseract OCR备用引擎
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    import os
    # 检查tesseract可执行文件是否存在
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        TESSERACT_AVAILABLE = True
        print("SUCCESS: Tesseract OCR engine initialized")
    else:
        print("WARNING: Tesseract not installed")
except ImportError:
    print("WARNING: pytesseract not installed")


class TesseractOCR:
    """
    Tesseract OCR引擎（备用方案）
    需要单独安装Tesseract可执行文件
    """

    def __init__(self, lang="chi_sim+eng"):
        """
        初始化Tesseract OCR引擎

        Args:
            lang: 语言设置，默认为中英文混合 "chi_sim+eng"
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract OCR not available, please install Tesseract executable")

        self.lang = lang
        print("SUCCESS: Using Tesseract OCR engine")

    def recognize_text_only(self, pil_image):
        """
        使用Tesseract进行文本识别

        Args:
            pil_image: PIL图像对象

        Returns:
            识别出的文本字符串
        """
        try:
            import pytesseract
            # 转换为灰度图像提高识别率
            if pil_image.mode != "L":
                pil_image = pil_image.convert("L")

            # 执行OCR识别
            text = pytesseract.image_to_string(pil_image, lang=self.lang)

            # 清理结果
            return clean_ocr_text(text)

        except Exception as e:
            print(f"Tesseract OCR识别失败: {e}")
            return ""


def capture_window_region(monitor_number=1, region=None):
    """
    使用mss极速截图指定区域

    Args:
        monitor_number: 显示器编号，默认为1
        region: 区域字典，格式: {'top': 100, 'left': 100, 'width': 400, 'height': 800}
                如果为None，则截取整个显示器

    Returns:
        PIL图像对象
    """
    with mss.mss() as sct:
        if region:
            monitor = region
        else:
            monitor = sct.monitors[monitor_number]

        # 极速截图
        sct_img = sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


def capture_active_window():
    """
    截取活动窗口

    Returns:
        PIL图像对象
    """
    try:
        import win32gui
        import win32ui
        from ctypes import windll

        # 获取活动窗口句柄
        hwnd = win32gui.GetForegroundWindow()

        # 获取窗口矩形
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        # 计算区域
        region = {
            "top": top,
            "left": left,
            "width": width,
            "height": height
        }

        return capture_window_region(region=region)

    except ImportError:
        print("需要安装pywin32: pip install pywin32")
        return None
    except Exception as e:
        print(f"截取活动窗口失败: {e}")
        return None


def extract_english_words(text):
    """
    从OCR文本中提取英语单词

    Args:
        text: OCR识别的文本

    Returns:
        英语单词列表
    """
    import re
    # 匹配英语单词（包括连字符）
    english_words = re.findall(r'[a-zA-Z]+(?:-[a-zA-Z]+)*', text)
    return [word for word in english_words if len(word) > 1]  # 过滤单个字母


def extract_chinese_text(text):
    """
    从OCR文本中提取中文字符

    Args:
        text: OCR识别的文本

    Returns:
        中文字符列表
    """
    import re
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    return chinese_chars


def clean_ocr_text(text):
    """
    清理OCR文本，去除无意义字符

    Args:
        text: OCR识别的原始文本

    Returns:
        清理后的文本
    """
    # 去除特殊字符，保留字母、数字、中文和基本标点
    import re
    cleaned = re.sub(r'[^\w\s\u4e00-\u9fff,，.。!！?？]', '', text)
    # 去除多余空格
    cleaned = ' '.join(cleaned.split())
    return cleaned


def test_ocr():
    """
    测试OCR功能
    """
    print("正在测试Windows原生OCR引擎...")

    try:
        # 创建中文OCR引擎
        print("1. 创建中文OCR引擎...")
        ocr_cn = WindowsOCR("zh-Hans-CN")
        print("✓ 中文OCR引擎创建成功")

        # 创建英文OCR引擎
        print("2. 创建英文OCR引擎...")
        ocr_en = WindowsOCR("en-US")
        print("✓ 英文OCR引擎创建成功")

        # 测试截图功能
        print("3. 测试截图功能...")
        screenshot = capture_window_region()
        print(f"✓ 截图成功，尺寸: {screenshot.size}")

        # 测试识别功能
        print("4. 测试OCR识别...")
        results = ocr_cn.recognize_text_only(screenshot)
        print(f"✓ 识别成功，结果: {results[:100]}...")

        print("\n所有测试通过！OCR引擎准备就绪。")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


if __name__ == "__main__":
    test_ocr()