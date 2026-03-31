#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocabGo RPA OCR Engine v2.0
基于NormCap项目的技术实现，使用Tesseract OCR命令行工具
支持图像预处理、详细结果解析和多语言识别
"""

import csv
import ctypes
import enum
import functools
import logging
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, List, Dict, Optional, Union, Tuple

# 图像处理库
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("WARNING: PIL/Pillow not available, image preprocessing disabled")

# 截图库
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("WARNING: mss not available, screenshot functionality disabled")

logger = logging.getLogger(__name__)


# ==================== Tesseract 参数配置 ====================

@enum.unique
class PSM(enum.IntEnum):
    """Tesseract 页面分割模式 (Page Segmentation Mode)"""

    OSD_ONLY = 0  # 仅方向和脚本检测 (OSD)
    AUTO_OSD = 1  # 自动页面分割，包含方向和脚本检测
    AUTO_ONLY = 2  # 自动页面分割，无OSD或OCR
    AUTO = 3  # 完全自动页面分割，无OSD (默认)
    SINGLE_COLUMN = 4  # 假设单一列文本，大小可变
    SINGLE_BLOCK_VERT_TEXT = 5  # 假设单个垂直对齐文本块
    SINGLE_BLOCK = 6  # 假设单个统一文本块
    SINGLE_LINE = 7  # 将图像视为单行文本
    SINGLE_WORD = 8  # 将图像视为单个单词
    CIRCLE_WORD = 9  # 将图像视为圆形中的单个单词
    SINGLE_CHAR = 10  # 将图像视为单个字符
    SPARSE_TEXT = 11  # 以任何顺序查找尽可能多的文本
    SPARSE_TEXT_OSD = 12  # 稀疏文本，包含方向和脚本检测
    RAW_LINE = 13  # 将图像视为单行文本，绕过Tesseract黑客技巧
    COUNT = 14  # 枚举条目数量

@enum.unique
class OEM(enum.IntEnum):
    """Tesseract OCR引擎模式 (OCR Engine Mode)"""

    TESSERACT_ONLY = 0  # 仅运行Tesseract - 最快
    LSTM_ONLY = 1  # 仅运行LSTM行识别器 (>=v4.00)
    TESSERACT_LSTM_COMBINED = 2  # 运行LSTM识别器，但在困难时允许回退到Tesseract (>=v4.00)
    DEFAULT = 3  # 运行两者并组合结果 - 最佳准确率


@dataclass
class TessArgs:
    """调用Tesseract时使用的参数"""

    tessdata_path: Optional[Union[str, Path]] = None
    lang: str = "chi_sim+eng"  # 中英文混合
    oem: OEM = OEM.DEFAULT
    psm: PSM = PSM.AUTO

    def as_list(self) -> List[str]:
        """生成Tesseract命令行参数"""
        arg_list = [
            "-l", self.lang,
            "--oem", str(self.oem.value),
            "--psm", str(self.psm.value),
        ]
        if self.tessdata_path:
            arg_list.extend(["--tessdata-dir", str(self.tessdata_path)])
        return arg_list


@dataclass
class OcrResult:
    """OCR识别结果，包含文本和元数据"""

    args: TessArgs
    words: List[Dict]  # OCR检测到的单词+元数据
    image: Optional[object] = None  # 原始图像对象

    @property
    def mean_conf(self) -> float:
        """OCR置信度平均值"""
        if conf_values := [float(w.get("conf", 0)) for w in self.words]:
            return sum(conf_values) / len(conf_values)
        return 0

    @property
    def text(self) -> str:
        """OCR识别的完整文本"""
        return self.add_linebreaks()

    def add_linebreaks(
        self,
        block_sep: str = "\n\n",
        par_sep: str = "\n",
        line_sep: str = "\n",
        word_sep: str = " ",
    ) -> str:
        """添加换行符的OCR文本

        当使用默认分隔符时，输出应该等于Tesseract CLI的输出
        """
        last_block_num = None
        last_par_num = None
        last_line_num = None
        text = ""

        for word in self.words:
            block_num = word.get("block_num", None)
            par_num = word.get("par_num", None)
            line_num = word.get("line_num", None)

            if block_num != last_block_num:
                text += block_sep + word["text"]
            elif par_num != last_par_num:
                text += par_sep + word["text"]
            elif line_num != last_line_num:
                text += line_sep + word["text"]
            else:
                text += word_sep + word["text"]

            last_block_num = block_num
            last_par_num = par_num
            last_line_num = line_num

        return text.strip()

    @property
    def num_chars(self) -> int:
        """字符数量（不包含分隔符）"""
        return sum(len(w["text"]) for w in self.words)

    @property
    def num_lines(self) -> int:
        """行数"""
        unique_lines = {w.get("line_num", None) for w in self.words}
        return len(unique_lines)

    @property
    def num_pars(self) -> int:
        """段落数量"""
        unique_pars = {w.get("par_num", None) for w in self.words}
        return len(unique_pars)

    @property
    def num_blocks(self) -> int:
        """文本块数量"""
        unique_blocks = {w.get("block_num", None) for w in self.words}
        return len(unique_blocks)


# ==================== Windows 路径处理 ====================

def get_short_path(long_path: str) -> str:
    """将长Windows路径转换为短8.3路径格式

    这对于包含特殊UTF-8字符的路径是必要的，
    这些字符无法被Windows上的Tesseract二进制文件作为参数处理。
    """
    if sys.platform != "win32":
        raise NotImplementedError("_get_short_path_as_str() 仅支持Windows")

    # 绑定 Win32 API
    _GetShortPathName = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathName.argtypes = [
        ctypes.wintypes.LPCWSTR,  # lpLongPath
        ctypes.wintypes.LPWSTR,  # lpShortPath
        ctypes.wintypes.DWORD,  # cchBuffer
    ]
    _GetShortPathName.restype = ctypes.wintypes.DWORD

    # 第一次调用以获取所需缓冲区大小
    needed = _GetShortPathName(long_path, None, 0)
    if needed == 0:
        raise ctypes.WinError()

    # 分配缓冲区并获取短路径
    buf = ctypes.create_unicode_buffer(needed)
    result = _GetShortPathName(long_path, buf, needed)
    if result == 0:
        raise ctypes.WinError()

    return buf.value


# ==================== Tesseract 引擎 ====================

class TesseractEngine:
    """基于Tesseract命令行的OCR引擎

    参考NormCap项目实现，直接调用tesseract.exe而非使用pytesseract
    """

    def __init__(self, tessdata_path: Optional[str] = None, lang: str = "chi_sim+eng"):
        """
        初始化Tesseract引擎

        Args:
            tessdata_path: Tesseract数据目录路径
            lang: 识别语言，默认为中英文混合 "chi_sim+eng"
        """
        self.tesseract_cmd = self._find_tesseract()
        self.tessdata_path = tessdata_path
        self.lang = lang
        self.oem = OEM.DEFAULT
        self.psm = PSM.AUTO

        logger.info(f"Tesseract引擎初始化: {self.tesseract_cmd}")
        logger.info(f"语言设置: {lang}")

        # 验证Tesseract可用性
        self._verify_tesseract()

    def _find_tesseract(self) -> str:
        """查找系统中的Tesseract可执行文件"""
        # 优先检查环境变量TESSDATA_PREFIX
        if tessdata_prefix := os.environ.get("TESSDATA_PREFIX"):
            tess_path = Path(tessdata_prefix)
            exe_path = tess_path / "tesseract.exe"
            if exe_path.exists():
                logger.info(f"Tesseract从TESSDATA_PREFIX找到: {exe_path}")
                return str(exe_path)

        # 检查常见安装位置
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]

        for path in common_paths:
            if Path(path).exists():
                logger.info(f"Tesseract从常见路径找到: {path}")
                return path

        # 检查PATH环境变量
        import shutil
        if tesseract_bin := shutil.which("tesseract"):
            logger.info(f"Tesseract从PATH找到: {tesseract_bin}")
            return tesseract_bin

        # 如果都找不到，给出详细的错误信息
        error_msg = "无法找到Tesseract可执行文件！\n"
        error_msg += "请检查以下位置：\n"
        for path in common_paths:
            exists = "SUCCESS 存在" if Path(path).exists() else "FAILED 不存在"
            error_msg += f"  {exists}: {path}\n"

        error_msg += f"\n或者设置TESSDATA_PREFIX环境变量指向Tesseract目录\n"
        error_msg += f"下载地址: https://github.com/UB-Mannheim/tesseract/wiki"

        raise FileNotFoundError(error_msg)

    def _verify_tesseract(self) -> None:
        """验证Tesseract是否可用"""
        try:
            result = subprocess.run(
                [self.tesseract_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            if result.returncode != 0:
                raise RuntimeError(f"Tesseract版本检查失败: {result.stderr}")

            logger.info(f"Tesseract版本: {result.stdout.strip()}")

        except FileNotFoundError:
            raise FileNotFoundError(f"无法找到Tesseract: {self.tesseract_cmd}")
        except Exception as e:
            logger.warning(f"Tesseract验证警告: {e}")

    def set_language(self, lang: str) -> None:
        """设置OCR语言"""
        self.lang = lang
        logger.info(f"语言设置为: {lang}")

    def set_psm(self, psm: PSM) -> None:
        """设置页面分割模式"""
        self.psm = psm
        logger.info(f"PSM设置为: {psm.name}")

    def set_oem(self, oem: OEM) -> None:
        """设置OCR引擎模式"""
        self.oem = oem
        logger.info(f"OEM设置为: {oem.name}")

    def _run_tesseract(
        self, image_path: str, output_path: str, args: List[str]
    ) -> List[List[str]]:
        """运行Tesseract命令

        Args:
            image_path: 输入图像文件路径
            output_path: 输出文件路径（不含扩展名）
            args: 额外的Tesseract参数

        Returns:
            TSV格式的识别结果
        """
        cmd_args = [
            str(self.tesseract_cmd),
            image_path,
            output_path,  # 输出文件名（会被添加.tsv扩展名）
            "-c", "tessedit_create_tsv=1",  # TSV格式输出
            *args,
        ]

        logger.debug(f"执行Tesseract命令: {' '.join(cmd_args)}")

        try:
            proc = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            if proc.returncode != 0:
                error_msg = f"Tesseract执行失败 (退出码 {proc.returncode})"
                if proc.stderr:
                    error_msg += f": {proc.stderr}"
                raise RuntimeError(error_msg)

        except subprocess.TimeoutExpired:
            raise RuntimeError("Tesseract执行超时")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"无法找到Tesseract可执行文件: {e}")

        # 读取TSV输出文件
        tsv_file = f"{output_path}.tsv"
        try:
            with open(tsv_file, encoding="utf-8") as fh:
                tsv_reader = csv.reader(fh, delimiter="\t", quotechar=None)
                lines = list(tsv_reader)
        except FileNotFoundError:
            raise RuntimeError(f"Tesseract未生成输出文件: {tsv_file}")

        return lines

    def recognize(self, image, preprocess: bool = True) -> OcrResult:
        """执行OCR识别

        Args:
            image: 图像对象（PIL.Image或文件路径）
            preprocess: 是否进行图像预处理

        Returns:
            OcrResult: 包含识别结果和元数据
        """
        # 处理图像输入
        if isinstance(image, (str, Path)):
            if PIL_AVAILABLE:
                image = Image.open(str(image))
            else:
                raise RuntimeError("需要PIL库来处理图像文件")

        if not PIL_AVAILABLE:
            raise RuntimeError("需要PIL/Pillow库进行图像处理")

        # 图像预处理
        processed_image = image
        if preprocess:
            processed_image = self._preprocess_image(image)

        # 准备参数
        tess_args = TessArgs(
            tessdata_path=self.tessdata_path,
            lang=self.lang,
            oem=self.oem,
            psm=self.psm,
        )

        # 保存临时图像
        with tempfile.TemporaryDirectory() as temp_dir:
            input_image_path = os.path.join(temp_dir, "vocabgo_ocr_input.png")
            output_path = os.path.join(temp_dir, "vocabgo_ocr_output")

            # Windows路径处理
            temp_input_path = input_image_path
            if sys.platform == "win32":
                try:
                    temp_input_path = get_short_path(input_image_path)
                except Exception:
                    logger.warning("短路径转换失败，使用原始路径")

            # 保存处理后的图像
            processed_image.save(input_image_path)

            # 运行Tesseract
            tsv_lines = self._run_tesseract(
                image_path=temp_input_path,
                output_path=output_path,
                args=tess_args.as_list()
            )

            # 解析TSV结果
            words = self._parse_tsv_result(tsv_lines)

            return OcrResult(
                args=tess_args,
                words=words,
                image=image,
            )

    def _preprocess_image(self, image) -> Image.Image:
        """图像预处理

        基于NormCap的实现，添加padding和调整大小以提高识别准确率

        Args:
            image: PIL.Image对象

        Returns:
            预处理后的图像
        """
        try:
            # 转换为RGB格式
            if image.mode != "RGB":
                image = image.convert("RGB")

            # 添加边距（padding）- Tesseract对有一定边距的内容识别效果更好
            padding = 80
            bg_color = self._get_background_color(image)
            padded_image = Image.new(
                "RGB",
                (image.width + padding * 2, image.height + padding * 2),
                bg_color
            )
            padded_image.paste(image, (padding, padding))

            # 调整图像大小 - 目标是等效300dpi分辨率
            # 根据研究，Tesseract在大写字符高度20-50px时效果最佳
            resize_factor = 2.0
            resized_image = padded_image.resize(
                (int(padded_image.width * resize_factor),
                int(padded_image.height * resize_factor)),
                Image.Resampling.LANCZOS
            )

            return resized_image

        except Exception as e:
            logger.warning(f"图像预处理失败: {e}，使用原始图像")
            return image

    def _get_background_color(self, image: Image.Image) -> Tuple[int, int, int]:
        """启发式地找到用于padding的背景颜色

        通过分析图像边缘像素，使用最常见的颜色作为背景
        """
        try:
            # 采样边缘像素
            edge_pixels = []

            # 上边缘
            for x in range(0, image.width, max(1, image.width // 50)):
                edge_pixels.append(image.getpixel((x, 0)))

            # 下边缘
            for x in range(0, image.width, max(1, image.width // 50)):
                edge_pixels.append(image.getpixel((x, image.height - 1)))

            # 左边缘
            for y in range(0, image.height, max(1, image.height // 50)):
                edge_pixels.append(image.getpixel((0, y)))

            # 右边缘
            for y in range(0, image.height, max(1, image.height // 50)):
                edge_pixels.append(image.getpixel((image.width - 1, y)))

            # 使用最频繁的颜色
            color_count = Counter(edge_pixels)
            most_common = color_count.most_common(1)[0][0]
            return most_common[:3]  # RGB tuple

        except Exception as e:
            logger.warning(f"背景颜色检测失败: {e}，使用白色背景")
            return (255, 255, 255)

    def _parse_tsv_result(self, tsv_lines: List[List[str]]) -> List[Dict]:
        """解析TSV格式的OCR结果

        TSV格式包含以下字段：
        - level: 层级 (1=页面, 2=块, 3=段落, 4=行, 5=单词)
        - page_num: 页码
        - block_num: 块编号
        - par_num: 段落编号
        - line_num: 行编号
        - word_num: 单词编号
        - left, top, width, height: 边界框坐标
        - conf: 置信度 (0-100)
        - text: 识别的文本
        """
        if not tsv_lines:
            return []

        # 第一行是标题
        headers = tsv_lines[0]
        words = []

        for line in tsv_lines[1:]:
            word_dict = {}
            for i, (header, value) in enumerate(zip(headers, line)):
                try:
                    if header in ["left", "top", "width", "height"]:
                        word_dict[header] = int(value)
                    elif header == "conf":
                        word_dict[header] = float(value)
                    else:
                        word_dict[header] = value
                except (ValueError, TypeError) as e:
                    logger.debug(f"解析字段 {header}={value} 失败: {e}")
                    word_dict[header] = value

            # 只添加非空文本
            if word_dict.get("text", "").strip():
                words.append(word_dict)

        return words

    def recognize_text_only(self, image, preprocess: bool = True) -> str:
        """仅返回文本，不包含元数据

        Args:
            image: 图像对象
            preprocess: 是否进行预处理

        Returns:
            识别的文本字符串
        """
        result = self.recognize(image, preprocess)
        return result.text


# ==================== 辅助函数 ====================

def capture_window_region(
    monitor_number: int = 1, region: Optional[Dict[str, int]] = None
) -> Optional[Image.Image]:
    """
    使用mss极速截图指定区域

    Args:
        monitor_number: 显示器编号，默认为1
        region: 区域字典，格式: {'top': 100, 'left': 100, 'width': 400, 'height': 800}
                如果为None，则截取整个显示器

    Returns:
        PIL图像对象，如果mss不可用则返回None
    """
    if not MSS_AVAILABLE:
        logger.error("mss库不可用，无法进行截图")
        return None

    try:
        with mss.mss() as sct:
            if region:
                monitor = region
            else:
                monitor = sct.monitors[monitor_number]

            # 极速截图
            sct_img = sct.grab(monitor)
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    except Exception as e:
        logger.error(f"截图失败: {e}")
        return None


def clean_ocr_text(text: str) -> str:
    """
    清理OCR文本，去除无意义字符

    Args:
        text: OCR识别的原始文本

    Returns:
        清理后的文本
    """
    # 去除特殊字符，保留字母、数字、中文和基本标点
    cleaned = re.sub(r'[^\w\s\u4e00-\u9fff,，。！？、；：""''（）《》]', '', text)
    # 去除多余空格
    cleaned = ' '.join(cleaned.split())
    return cleaned


def extract_english_words(text: str) -> List[str]:
    """
    从OCR文本中提取英语单词

    Args:
        text: OCR识别的文本

    Returns:
        英语单词列表
    """
    # 匹配英语单词（包括连字符）
    english_words = re.findall(r'[a-zA-Z]+(?:-[a-zA-Z]+)*', text)
    return [word for word in english_words if len(word) > 1]  # 过滤单个字母


def extract_chinese_text(text: str) -> List[str]:
    """
    从OCR文本中提取中文字符

    Args:
        text: OCR识别的文本

    Returns:
        中文字符列表
    """
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    return chinese_chars


# ==================== 便捷类 ====================

class VocabGoOCR:
    """VocabGo OCR 便捷接口类"""

    def __init__(self, tessdata_path: Optional[str] = None, lang: str = "chi_sim+eng"):
        """
        初始化OCR引擎

        Args:
            tessdata_path: Tesseract数据目录路径
            lang: 识别语言，默认为中英文混合
        """
        try:
            self.engine = TesseractEngine(tessdata_path=tessdata_path, lang=lang)
            self.available = True
            logger.info("SUCCESS VocabGo OCR引擎初始化成功")
        except Exception as e:
            self.engine = None
            self.available = False
            logger.error(f"FAILED VocabGo OCR引擎初始化失败: {e}")

    def recognize(self, image, preprocess: bool = True) -> Optional[OcrResult]:
        """执行OCR识别"""
        if not self.available:
            logger.error("OCR引擎不可用")
            return None

        try:
            return self.engine.recognize(image, preprocess=preprocess)
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return None

    def recognize_text_only(self, image, preprocess: bool = True) -> Optional[str]:
        """仅返回识别的文本"""
        if not self.available:
            logger.error("OCR引擎不可用")
            return None

        try:
            return self.engine.recognize_text_only(image, preprocess=preprocess)
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return None


# ==================== 测试函数 ====================

def test_ocr():
    """测试OCR功能"""
    print("正在测试VocabGo OCR引擎...")

    try:
        # 创建OCR引擎
        print("1. 创建OCR引擎...")
        ocr = VocabGoOCR(lang="chi_sim+eng")
        if not ocr.available:
            print("FAILED: OCR engine creation failed")
            return False

        print("SUCCESS OCR引擎创建成功")

        # 测试截图功能
        print("2. 测试截图功能...")
        screenshot = capture_window_region()
        if not screenshot:
            print("FAILED 截图功能失败")
            return False

        print(f"SUCCESS 截图成功，尺寸: {screenshot.size}")

        # 测试识别功能
        print("3. 测试OCR识别...")
        result = ocr.recognize(screenshot, preprocess=True)
        if not result:
            print("FAILED OCR识别失败")
            return False

        print(f"SUCCESS OCR识别成功")
        print(f"   识别文本: {result.text[:100]}...")
        print(f"   平均置信度: {result.mean_conf:.1f}%")
        print(f"   字符数: {result.num_chars}")
        print(f"   行数: {result.num_lines}")

        print("\n所有测试通过！OCR引擎准备就绪。")
        return True

    except Exception as e:
        print(f"FAILED 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_ocr()