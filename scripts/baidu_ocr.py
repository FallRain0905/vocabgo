#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度OCR识别器
基于百度智能云API的通用文字识别
"""

import requests
import base64
import io
from typing import Optional
from PIL import Image


class BaiduOCR:
    """百度OCR识别器"""

    def __init__(self, api_key: str, secret_key: str):
        """
        初始化百度OCR

        Args:
            api_key: 百度API Key
            secret_key: 百度Secret Key
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.token = None
        self.api_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"

    def get_access_token(self) -> Optional[str]:
        """获取访问Token"""
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
            result = response.json()

            if "access_token" in result:
                self.token = result["access_token"]
                return self.token
            else:
                error = result.get("error_description", "Unknown error")
                print(f"[ERROR] 百度OCR Token获取失败: {error}")
                return None
        except Exception as e:
            print(f"[ERROR] 百度OCR Token请求失败: {e}")
            return None

    def recognize(self, image: Image, preprocess: bool = True) -> Optional[dict]:
        """
        识别图片中的文字

        Args:
            image: PIL Image对象
            preprocess: 是否预处理图像（暂时未实现）

        Returns:
            识别结果字典，包含text, confidence等
        """
        token = self.get_access_token()
        if not token:
            return {
                "success": False,
                "error": "无法获取访问Token"
            }

        try:
            # 将PIL图像转换为字节流
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            # Base64编码
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # 构建请求数据
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'image': img_base64
            }

            # 调用百度OCR API
            url = f"{self.api_url}?access_token={token}"
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            # 解析结果
            if "error_code" in result and result["error_code"] != 0:
                error_msg = result.get("error_msg", "Unknown error")
                print(f"[ERROR] 百度OCR识别失败: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

            # 提取文字结果
            if "words_result" in result:
                words = [word["words"] for word in result["words_result"]]
                text = "\n".join(words)
                print(f"[INFO] 百度OCR识别成功: {len(words)}个词")
                return {
                    "success": True,
                    "text": text,
                    "words_count": len(words),
                    "engine": "baidu"
                }
            else:
                return {
                    "success": False,
                    "error": "未知响应格式"
                }

        except requests.exceptions.Timeout:
            print(f"[ERROR] 百度OCR请求超时")
            return {
                "success": False,
                "error": "请求超时"
            }
        except Exception as e:
            print(f"[ERROR] 百度OCR识别异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def recognize_text_only(self, image: Image, preprocess: bool = True) -> Optional[str]:
        """仅返回识别的文本，简化接口"""
        result = self.recognize(image, preprocess)
        if result.get("success") and result.get("text"):
            return result["text"]
        elif result.get("error"):
            return f"[ERROR] {result['error']}"
        else:
            return "[ERROR] 识别失败"


# 测试代码
if __name__ == "__main__":
    # 测试配置（用户提供的）
    API_KEY = "x8o9repM7KgO525AiyzeFGma"
    SECRET_KEY = "i6hr5CVKwieQcnbVdwX8TqOHQYI8wPar"

    # 创建百度OCR实例
    ocr = BaiduOCR(API_KEY, SECRET_KEY)

    print("百度OCR测试")
    print("=" * 50)

    # 测试获取Token
    print("\n1. 测试获取Token...")
    token = ocr.get_access_token()
    if token:
        print(f"[SUCCESS] Token获取成功: {token[:20]}...")
    else:
        print("[FAILED] Token获取失败")
        exit(1)

    # 测试文字识别
    print("\n2. 测试文字识别...")
    test_image = Image.new('RGB', (400, 200), color='white')
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(test_image)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    draw.text((50, 80), "Hello 百度OCR", fill='black', font=font)

    result = ocr.recognize(test_image)
    if result.get("success"):
        print(f"[SUCCESS] 识别成功!")
        print(f"识别文本: {result['text']}")
        print(f"词数: {result['words_count']}")
    else:
        print(f"[FAILED] 识别失败: {result.get('error')}")

    print("\n" + "=" * 50)
