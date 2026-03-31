#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocabGo RPA 打包成EXE程序
支持一键打包，生成可执行文件
"""

import os
import sys
import subprocess
from pathlib import Path

def create_spec_file():
    """创建PyInstaller配置文件"""

    spec_content = r"""# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(SPECPATH).parent.parent

# 分析主程序
a = Analysis(
    [project_root / 'scripts' / 'translator_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 配置文件
        (str(project_root / 'config'), 'config'),
        # 资源文件
        (str(project_root / 'assets'), 'assets'),
        # 文档文件
        (str(project_root / 'docs'), 'docs'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'requests',
        'json',
        'threading',
        'numpy',
        'sounddevice',
        'soundfile',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'mss',
        'keyboard',
        'cv2',
        # OCR相关
        'scripts.ocr_engine_v2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.testing',
        'unittest',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=0,
)

# 处理pyqt相关（如果有）
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VocabGo_RPA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icon.ico'),  # 需要准备图标文件
)

# 收集所有文件到一个目录
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VocabGo_RPA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
)
"""

    spec_path = Path(__file__).parent / 'vocabgo_rpa.spec'
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"✓ Spec文件创建成功: {spec_path}")
    return spec_path

def prepare_assets():
    """准备打包所需的资源文件"""

    project_root = Path(__file__).parent.parent
    assets_dir = project_root / 'assets'

    # 确保assets目录存在
    assets_dir.mkdir(exist_ok=True)

    # 检查图标文件
    icon_path = assets_dir / 'icon.ico'
    if not icon_path.exists():
        print("⚠️ 图标文件不存在，将使用默认图标")
        # 可以在这里创建默认图标

    # 检查README文件
    readme_path = project_root / 'README.md'
    if not readme_path.exists():
        print("⚠️ README文件不存在")

    # 检查依赖文件
    requirements_path = project_root / 'requirements.txt'
    if not requirements_path.exists():
        print("⚠️ requirements.txt文件不存在")

    print("✓ 资源文件检查完成")

def install_dependencies():
    """安装打包所需的依赖"""

    print("正在检查PyInstaller安装...")

    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'pyinstaller'],
            check=True
        )
        print("✓ PyInstaller安装成功")

def build_exe():
    """执行打包"""

    print("\n" + "=" * 50)
    print("开始打包VocabGo RPA")
    print("=" * 50)

    # 创建spec文件
    spec_path = create_spec_file()

    # 准备资源
    prepare_assets()

    # 执行PyInstaller
    try:
        print("\n正在执行PyInstaller...")
        subprocess.run(
            [sys.executable, '-m', 'PyInstaller', str(spec_path)],
            check=True,
            cwd=Path(__file__).parent
        )

        print("\n" + "=" * 50)
        print("打包完成！")
        print("=" * 50)

        # 查找生成的文件
        build_dir = Path(__file__).parent / 'dist' / 'VocabGo_RPA'
        if build_dir.exists():
            print(f"✓ 打包文件位置: {build_dir}")
            print(f"  可执行文件: {build_dir / 'VocabGo_RPA.exe'}")

            # 显示文件大小
            exe_size = (build_dir / 'VocabGo_RPA.exe').stat().st_size / (1024 * 1024)
            print(f"  文件大小: {exe_size:.2f} MB")

            # 显示后续步骤
            print("\n" + "=" * 50)
            print("后续步骤：")
            print("=" * 50)
            print("1. 测试exe文件是否正常工作")
            print("2. 将Tesseract放入程序目录")
            print("3. 创建安装程序或发布zip包")
            print("4. 编写使用说明文档")

        else:
            print("✗ 打包目录不存在")

    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        print("\n请检查错误信息并重试")

def create_portable_package():
    """创建便携版zip包"""

    build_dir = Path(__file__).parent / 'dist' / 'VocabGo_RPA'
    if not build_dir.exists():
        print("⚠️ 打包目录不存在，先执行打包")
        return

    import zipfile
    from datetime import datetime

    # 创建zip文件
    version = datetime.now().strftime("%Y%m%d")
    zip_name = f"VocabGo_RPA_v{version}_portable.zip"
    zip_path = Path(__file__).parent / 'dist' / zip_name

    print(f"\n正在创建便携版: {zip_name}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加所有文件
        for file_path in build_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)

    # 计算文件大小
    zip_size = zip_path.stat().st_size / (1024 * 1024)
    print(f"✓ 便携版创建成功: {zip_path}")
    print(f"  文件大小: {zip_size:.2f} MB")

def main():
    """主函数"""

    print("VocabGo RPA 打包工具")
    print("=" * 50)

    try:
        # 安装依赖
        install_dependencies()

        # 执行打包
        build_exe()

        # 询问是否创建便携版
        print("\n是否创建便携版zip包？(y/n): ", end='')
        choice = input().strip().lower()

        if choice == 'y':
            create_portable_package()

        print("\n" + "=" * 50)
        print("打包流程完成！")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n用户中断打包")
    except Exception as e:
        print(f"\n打包过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()