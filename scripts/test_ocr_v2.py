#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocabGo OCR Engine v2.0 测试脚本
基于NormCap技术的Tesseract OCR测试
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ocr_engine_v2 import (
    VocabGoOCR, capture_window_region,
    extract_english_words, clean_ocr_text,
    TesseractEngine, OEM, PSM
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_imports():
    """测试导入"""
    print("=" * 50)
    print("Testing Imports")
    print("=" * 50)

    try:
        from scripts.ocr_engine_v2 import VocabGoOCR, TesseractEngine, PSM, OEM
        print("SUCCESS: All imports successful")
        return True
    except Exception as e:
        print(f"FAILED: Import error - {e}")
        return False

def test_tesseract_engine():
    """测试Tesseract引擎初始化"""
    print("\n" + "=" * 50)
    print("Testing Tesseract Engine")
    print("=" * 50)

    try:
        # 创建Tesseract引擎
        engine = TesseractEngine(lang="chi_sim+eng")
        print(f"SUCCESS: Tesseract engine created")
        print(f"  Path: {engine.tesseract_cmd}")
        print(f"  Language: {engine.lang}")
        print(f"  OEM: {engine.oem.name}")
        print(f"  PSM: {engine.psm.name}")
        return True, engine
    except Exception as e:
        print(f"FAILED: {e}")
        return False, None

def test_vocabcocr():
    """测试VocabGo OCR便捷类"""
    print("\n" + "=" * 50)
    print("Testing VocabGo OCR")
    print("=" * 50)

    try:
        # 创建VocabGo OCR实例
        ocr = VocabGoOCR(lang="chi_sim+eng")
        print(f"SUCCESS: VocabGo OCR created")
        print(f"  Available: {ocr.available}")
        return True, ocr
    except Exception as e:
        print(f"FAILED: {e}")
        return False, None

def test_screenshot():
    """测试截图功能"""
    print("\n" + "=" * 50)
    print("Testing Screenshot")
    print("=" * 50)

    try:
        # 截取整个屏幕
        screenshot = capture_window_region()

        if screenshot:
            print(f"SUCCESS: Screenshot captured")
            print(f"  Size: {screenshot.size}")
            print(f"  Mode: {screenshot.mode}")
            return True, screenshot
        else:
            print("FAILED: Screenshot capture returned None")
            return False, None
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_ocr_recognition(ocr_engine, image):
    """测试OCR识别"""
    print("\n" + "=" * 50)
    print("Testing OCR Recognition")
    print("=" * 50)

    try:
        # 执行OCR识别（启用预处理）
        result = ocr_engine.recognize(image, preprocess=True)

        if result:
            print("SUCCESS: OCR recognition completed")
            print(f"  Text (first 100 chars): {result.text[:100]}")
            print(f"  Mean confidence: {result.mean_conf:.1f}%")
            print(f"  Characters: {result.num_chars}")
            print(f"  Lines: {result.num_lines}")
            print(f"  Paragraphs: {result.num_pars}")
            print(f"  Blocks: {result.num_blocks}")
            print(f"  Words detected: {len(result.words)}")

            if len(result.words) > 0:
                print(f"\n  Sample word details:")
                sample = result.words[0]
                print(f"    Text: '{sample.get('text', 'N/A')}'")
                print(f"    Confidence: {sample.get('conf', 0):.1f}%")
                print(f"    Position: ({sample.get('left', 0)}, {sample.get('top', 0)})")

            return True, result
        else:
            print("FAILED: OCR returned None")
            return False, None
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_text_processing():
    """测试文本处理功能"""
    print("\n" + "=" * 50)
    print("Testing Text Processing")
    print("=" * 50)

    try:
        # 测试文本清理
        test_text = "Hello 世界! This is a test. 这是一段测试文字。"
        cleaned = clean_ocr_text(test_text)
        print(f"SUCCESS: Text processing works")
        print(f"  Original: {test_text}")
        print(f"  Cleaned: {cleaned}")

        # 测试英语单词提取
        english_words = extract_english_words(test_text)
        print(f"  English words: {english_words}")

        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_tesseract_parameters():
    """测试Tesseract参数配置"""
    print("\n" + "=" * 50)
    print("Testing Tesseract Parameters")
    print("=" * 50)

    try:
        # 创建引擎
        engine = TesseractEngine(lang="chi_sim+eng")

        # 测试不同的PSM模式
        print("Testing different PSM modes:")
        for psm_mode in [PSM.AUTO, PSM.SINGLE_BLOCK, PSM.SINGLE_COLUMN]:
            engine.set_psm(psm_mode)
            print(f"  {psm_mode.name}: {psm_mode.value}")

        # 测试不同的OEM模式
        print("\nTesting different OEM modes:")
        for oem_mode in [OEM.DEFAULT, OEM.TESSERACT_ONLY, OEM.LSTM_ONLY]:
            engine.set_oem(oem_mode)
            print(f"  {oem_mode.name}: {oem_mode.value}")

        # 测试语言设置
        print("\nTesting language settings:")
        for lang in ["chi_sim+eng", "eng", "chi_sim"]:
            engine.set_language(lang)
            print(f"  Language: {lang}")

        print("SUCCESS: Parameter configuration works")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    """主测试函数"""
    print("VocabGo OCR Engine v2.0 - Test Suite")
    print("=" * 50)
    print("Based on NormCap technology implementation")
    print("=" * 50)

    results = []

    # 1. 测试导入
    import_success = test_imports()
    results.append(("Imports", import_success))

    if not import_success:
        print("\nCannot continue without successful imports")
        return

    # 2. 测试Tesseract引擎
    tess_success, tess_engine = test_tesseract_engine()
    results.append(("Tesseract Engine", tess_success))

    # 3. 测试VocabGo OCR
    ocr_success, ocr_instance = test_vocabcocr()
    results.append(("VocabGo OCR", ocr_success))

    # 4. 测试截图功能
    screen_success, screenshot = test_screenshot()
    results.append(("Screenshot", screen_success))

    # 5. 测试OCR识别
    if tess_success and screenshot:
        ocr_success, ocr_result = test_ocr_recognition(ocr_instance, screenshot)
        results.append(("OCR Recognition", ocr_success))
    else:
        results.append(("OCR Recognition", False))
        print("SKIPPED: OCR recognition (missing prerequisites)")

    # 6. 测试文本处理
    text_success = test_text_processing()
    results.append(("Text Processing", text_success))

    # 7. 测试Tesseract参数
    if tess_success:
        param_success = test_tesseract_parameters()
        results.append(("Tesseract Parameters", param_success))
    else:
        results.append(("Tesseract Parameters", False))
        print("SKIPPED: Tesseract parameters (Tesseract not available)")

    # 输出测试结果摘要
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, success in results:
        status = "PASS" if success else "FAIL" if "SKIPPED" not in str(success) else "SKIP"

        if status == "PASS":
            passed += 1
            print(f"[PASS] {test_name}")
        elif status == "FAIL":
            failed += 1
            print(f"[FAIL] {test_name}")
        else:
            skipped += 1
            print(f"[SKIP] {test_name}")

    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

    # 给出建议
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS")
    print("=" * 50)

    if passed == len(results):
        print("Excellent! All tests passed. OCR engine is ready to use.")
    elif passed >= len(results) * 0.7:  # 70%通过率
        print("Good! Most tests passed. OCR engine should work.")
        print("Some features may have issues. Check individual test results.")
    elif passed >= len(results) * 0.5:  # 50%通过率
        print("Partial success. OCR engine has some issues.")
        print("Focus on fixing the failed tests.")
    else:
        print("Major issues. OCR engine needs attention.")
        print("Please install Tesseract and configure environment variables.")

    print("\nSpecific recommendations:")

    if not results[1][1]:  # Tesseract Engine failed
        print("- Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        print("- Set TESSDATA_PREFIX environment variable")

    if not results[3][1]:  # Screenshot failed
        print("- Install mss: pip install mss")

    if not results[4][1]:  # OCR Recognition failed
        print("- Check Tesseract installation and language packs")
        print("- Ensure image quality and clear text")

    print("\nTest suite completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()