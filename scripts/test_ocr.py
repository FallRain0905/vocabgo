#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR功能测试脚本
用于验证OCR引擎的安装和功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入"""
    print("=" * 50)
    print("Testing OCR Imports")
    print("=" * 50)

    try:
        from scripts.ocr_engine import (
            WindowsOCR, TesseractOCR,
            WINSDK_AVAILABLE, TESSERACT_AVAILABLE,
            capture_window_region, clean_ocr_text
        )
        print("SUCCESS: All imports successful")
        return True, {
            'winsdk_available': WINSDK_AVAILABLE,
            'tesseract_available': TESSERACT_AVAILABLE
        }
    except Exception as e:
        print(f"FAILED: Import error - {e}")
        return False, {}

def test_windows_ocr():
    """测试Windows原生OCR"""
    print("\n" + "=" * 50)
    print("Testing Windows Native OCR")
    print("=" * 50)

    try:
        from scripts.ocr_engine import WINSDK_AVAILABLE, WindowsOCR

        if not WINSDK_AVAILABLE:
            print("SKIPPED: winsdk not installed")
            return False, "winsdk not available"

        ocr = WindowsOCR("zh-Hans-CN")
        print("SUCCESS: Windows OCR engine initialized")
        return True, "Windows OCR available"
    except Exception as e:
        print(f"FAILED: {e}")
        return False, str(e)

def test_tesseract_ocr():
    """测试Tesseract OCR"""
    print("\n" + "=" * 50)
    print("Testing Tesseract OCR")
    print("=" * 50)

    try:
        from scripts.ocr_engine import TESSERACT_AVAILABLE, TesseractOCR

        if not TESSERACT_AVAILABLE:
            print("SKIPPED: Tesseract not installed")
            return False, "Tesseract not available"

        ocr = TesseractOCR("chi_sim+eng")
        print("SUCCESS: Tesseract OCR engine initialized")
        return True, "Tesseract OCR available"
    except Exception as e:
        print(f"FAILED: {e}")
        return False, str(e)

def test_screenshot():
    """测试截图功能"""
    print("\n" + "=" * 50)
    print("Testing Screenshot Function")
    print("=" * 50)

    try:
        from scripts.ocr_engine import capture_window_region

        screenshot = capture_window_region()
        print(f"SUCCESS: Screenshot captured - Size: {screenshot.size}")
        return True, f"Screenshot size: {screenshot.size}"
    except Exception as e:
        print(f"FAILED: {e}")
        return False, str(e)

def test_text_processing():
    """测试文本处理功能"""
    print("\n" + "=" * 50)
    print("Testing Text Processing Functions")
    print("=" * 50)

    try:
        from scripts.ocr_engine import clean_ocr_text, extract_english_words

        test_text = "Hello 世界! This is a test. 这是一段测试文字。"
        cleaned = clean_ocr_text(test_text)
        english_words = extract_english_words(test_text)

        print(f"Original: {test_text}")
        print(f"Cleaned: {cleaned}")
        print(f"English words: {english_words}")
        print("SUCCESS: Text processing functions work")
        return True, "Text processing successful"
    except Exception as e:
        print(f"FAILED: {e}")
        return False, str(e)

def test_gui_integration():
    """测试GUI集成"""
    print("\n" + "=" * 50)
    print("Testing GUI Integration")
    print("=" * 50)

    try:
        # 检查GUI脚本是否有OCR相关导入
        gui_script = project_root / "scripts" / "translator_gui.py"
        with open(gui_script, 'r', encoding='utf-8') as f:
            gui_code = f.read()

        ocr_indicators = [
            'from scripts.ocr_engine import',
            'perform_ocr',
            'translate_ocr_content',
            'setup_ocr_hotkey'
        ]

        missing = []
        for indicator in ocr_indicators:
            if indicator not in gui_code:
                missing.append(indicator)

        if missing:
            print(f"FAILED: Missing OCR integrations: {missing}")
            return False, "GUI integration incomplete"

        print("SUCCESS: GUI has OCR integration")
        return True, "GUI integration complete"
    except Exception as e:
        print(f"FAILED: {e}")
        return False, str(e)

def main():
    """主测试函数"""
    print("VocabGo RPA OCR Test Suite")
    print("=" * 50)

    results = []

    # 1. 测试导入
    import_success, import_info = test_imports()
    results.append(("Imports", import_success, import_info))
    if not import_success:
        print("\nCannot continue without successful imports")
        return

    # 2. 测试Windows OCR
    win_success, win_info = test_windows_ocr()
    results.append(("Windows OCR", win_success, win_info))

    # 3. 测试Tesseract OCR
    tess_success, tess_info = test_tesseract_ocr()
    results.append(("Tesseract OCR", tess_success, tess_info))

    # 4. 测试截图功能
    screen_success, screen_info = test_screenshot()
    results.append(("Screenshot", screen_success, screen_info))

    # 5. 测试文本处理
    text_success, text_info = test_text_processing()
    results.append(("Text Processing", text_success, text_info))

    # 6. 测试GUI集成
    gui_success, gui_info = test_gui_integration()
    results.append(("GUI Integration", gui_success, gui_info))

    # 输出测试结果摘要
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, success, info in results:
        status = "PASS" if success else "FAIL" if "SKIPPED" not in info else "SKIP"

        if status == "PASS":
            passed += 1
            print(f"[PASS] {test_name}")
        elif status == "SKIP":
            skipped += 1
            print(f"[SKIP] {test_name} - {info}")
        else:
            failed += 1
            print(f"[FAIL] {test_name} - {info}")

    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

    # 给出建议
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS")
    print("=" * 50)

    if not import_info.get('winsdk_available') and not import_info.get('tesseract_available'):
        print("- No OCR engine available. Please install one:")
        print("  - Windows OCR: pip install winsdk (requires Visual Studio)")
        print("  - Tesseract OCR: Install Tesseract + pip install pytesseract")
    elif import_info.get('winsdk_available'):
        print("- Windows OCR available - Recommended for best performance")
    elif import_info.get('tesseract_available'):
        print("- Tesseract OCR available - Good alternative")
        print("- Consider installing Windows OCR for better performance")

    if gui_success:
        print("- GUI integration complete - OCR features ready to use")
    else:
        print("- GUI integration incomplete - check translator_gui.py")

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