#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VocabGo RPA 依赖下载器
自动下载和安装Tesseract OCR引擎和其他依赖
"""

import os
import sys
import urllib.request
import zipfile
import hashlib
from pathlib import Path
from typing import Optional, Callable
import threading
import json

# 尝试导入GUI库（用于进度显示）
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    GUI_AVAILABLE = True
except ImportError:
    import tkinter as tk
    GUI_AVAILABLE = False

# 依赖定义
DEPENDENCIES = {
    "tesseract": {
        "name": "Tesseract OCR引擎",
        "description": "文字识别核心引擎，支持中英文识别",
        "required": True,
        "size": "20 MB",
        "files": {
            "portable": {
                "url": "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.0/tesseract-ocr-w64-portable.zip",
                "filename": "tesseract-ocr-w64-portable.zip",
                "extract_to": "",
                "icon": "🔤"
            }
        },
        "language_chi_sim": {
            "url": "https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata",
            "filename": "chi_sim.traineddata",
            "extract_to": "tessdata",
            "icon": "🇨🇳",
            "size": "5 MB"
        },
        "language_eng": {
            "url": "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata",
            "filename": "eng.traineddata",
            "extract_to": "tessdata",
            "icon": "🇺🇸",
            "size": "2 MB"
        }
    }
}


class DependencyDownloader:
    """依赖下载器"""

    def __init__(self, install_dir: Optional[Path] = None):
        """
        初始化依赖下载器

        Args:
            install_dir: 安装目录，默认为程序目录下的dependencies
        """
        if install_dir is None:
            self.install_dir = Path(__file__).parent.parent / "dependencies"
        else:
            self.install_dir = Path(install_dir)

        self.install_dir.mkdir(parents=True, exist_ok=True)

        self.download_status = {}  # 下载状态
        self.total_size = 0
        self.downloaded_size = 0
        self.current_file = ""
        self.cancel_requested = False

    def check_dependencies(self) -> dict:
        """检查已安装的依赖"""
        status = {}

        # 检查Tesseract
        tesseract_exe = self.install_dir / "tesseract" / "tesseract.exe"
        status["tesseract"] = tesseract_exe.exists()

        # 检查中文语言包
        chi_sim_data = self.install_dir / "tessdata" / "chi_sim.traineddata"
        status["language_chi_sim"] = chi_sim_data.exists()

        # 检查英文语言包
        eng_data = self.install_dir / "tessdata" / "eng.traineddata"
        status["language_eng"] = eng_data.exists()

        return status

    def download_file(self, url: str, filename: str, progress_callback: Optional[Callable] = None) -> bool:
        """
        下载文件

        Args:
            url: 下载URL
            filename: 保存的文件名
            progress_callback: 进度回调函数(当前大小, 总大小, 当前文件名)

        Returns:
            是否下载成功
        """
        try:
            # 创建保存路径
            save_path = self.install_dir / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)

            self.current_file = filename

            def progress_hook(block_num, block_size, total_size):
                """下载进度回调"""
                if self.cancel_requested:
                    raise KeyboardInterrupt("下载已取消")

                current = block_num * block_size
                if total_size > 0:
                    percent = (current / total_size) * 100

                    # 更新进度
                    self.downloaded_size += block_size
                    if progress_callback:
                        progress_callback(self.downloaded_size, self.total_size + total_size, filename, percent)

            # 下载文件
            urllib.request.urlretrieve(url, str(save_path), reporthook=progress_hook)

            return True

        except Exception as e:
            print(f"下载失败: {e}")
            return False

    def extract_zip(self, zip_path: str, target_dir: str) -> bool:
        """解压zip文件"""
        try:
            full_zip_path = self.install_dir / zip_path
            full_target_dir = self.install_dir / target_dir

            with zipfile.ZipFile(full_zip_path, 'r') as zip_ref:
                zip_ref.extractall(full_target_dir)

            # 删除zip文件
            full_zip_path.unlink()

            return True

        except Exception as e:
            print(f"解压失败: {e}")
            return False

    def download_tesseract(self, progress_callback: Optional[Callable] = None) -> bool:
        """下载Tesseract OCR引擎"""
        print("开始下载Tesseract OCR引擎...")

        tesseract_config = DEPENDENCIES["tesseract"]

        # 下载便携版
        portable = tesseract_config["files"]["portable"]
        if not self.download_file(portable["url"], portable["filename"], progress_callback):
            return False

        # 解压
        if not self.extract_zip(portable["filename"], portable["extract_to"]):
            return False

        # 检查可执行文件
        tesseract_exe = self.install_dir / portable["extract_to"] / "tesseract.exe"
        if not tesseract_exe.exists():
            print("Tesseract可执行文件不存在")
            return False

        print("Tesseract OCR引擎下载完成")
        return True

    def download_language(self, lang_code: str, progress_callback: Optional[Callable] = None) -> bool:
        """下载语言包"""
        print(f"开始下载{lang_code}语言包...")

        lang_key = f"language_{lang_code}"
        if lang_key not in DEPENDENCIES["tesseract"]["files"]:
            print(f"未知语言: {lang_code}")
            return False

        lang_config = DEPENDENCIES["tesseract"]["files"][lang_key]

        # 下载语言包
        if not self.download_file(lang_config["url"], lang_config["filename"], progress_callback):
            return False

        print(f"{lang_code}语言包下载完成")
        return True

    def install_all_dependencies(self, progress_callback: Optional[Callable] = None) -> bool:
        """安装所有依赖"""
        try:
            # 检查已安装的依赖
            status = self.check_dependencies()

            print("\n当前依赖状态:")
            for dep, installed in status.items():
                icon = "✓" if installed else "✗"
                print(f"  {icon} {dep}")

            # 如果都安装了，直接返回
            if all(status.values()):
                print("\n所有依赖已安装！")
                return True

            # 计算需要下载的总大小
            total_download_size = 0
            for dep, installed in status.items():
                if not installed:
                    if dep in DEPENDENCIES["tesseract"]["files"]:
                        file_info = DEPENDENCIES["tesseract"]["files"][dep]
                        if "size" in file_info:
                            total_download_size += int(file_info["size"].replace(" MB", ""))

            print(f"\n需要下载总大小: ~{total_download_size} MB")

            # 下载Tesseract
            if not status["tesseract"]:
                print("\n正在下载Tesseract OCR引擎...")
                if not self.download_tesseract(progress_callback):
                    return False

            # 下载中文语言包
            if not status["language_chi_sim"]:
                print("\n正在下载中文语言包...")
                if not self.download_language("chi_sim", progress_callback):
                    return False

            # 下载英文语言包
            if not status["language_eng"]:
                print("\n正在下载英文语言包...")
                if not self.download_language("eng", progress_callback):
                    return False

            # 验证安装
            final_status = self.check_dependencies()
            if all(final_status.values()):
                print("\n✓ 所有依赖安装完成！")
                return True
            else:
                print("\n✗ 部分依赖安装失败")
                return False

        except Exception as e:
            print(f"安装依赖失败: {e}")
            return False

    def cancel_download(self):
        """取消下载"""
        self.cancel_requested = True


class DependencyInstallerGUI:
    """依赖安装GUI界面"""

    def __init__(self):
        self.root = None
        self.downloader = None
        self.progress_var = None
        self.status_var = None
        self.detail_var = None
        self.total_var = None
        self.cancel_button = None

    def show_dependency_check(self, install_callback: Callable[[], None]):
        """显示依赖检查对话框"""
        self.root = tk.Tk()
        self.root.title("VocabGo RPA - 依赖检查")
        self.root.geometry("600x400")
        self.root.configure(bg='#2D2D2D')
        self.root.attributes('-topmost', True)

        # 检查依赖
        downloader = DependencyDownloader()
        status = downloader.check_dependencies()

        # 创建主界面
        main_frame = tk.Frame(self.root, bg='#2D2D2D', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="📦 依赖检查",
            bg='#2D2D2D',
            fg='#4FC3F7',
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # 状态列表
        status_frame = tk.Frame(main_frame, bg='#2D2D2D')
        status_frame.pack(fill=tk.X, pady=(0, 20))

        tesseract_config = DEPENDENCIES["tesseract"]

        # Tesseract状态
        tesseract_status = "✓ 已安装" if status["tesseract"] else "✗ 未安装"
        tk.Label(
            status_frame,
            text=f"{tesseract_config['files']['portable']['icon']} Tesseract OCR引擎",
            bg='#2D2D2D', fg='white',
            font=('Arial', 11)
        ).pack(anchor=tk.W)

        tk.Label(
            status_frame,
            text=f"   {tesseract_status} ({tesseract_config['size']})",
            bg='#2D2D2D', fg='#9E9E9E',
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=(0, 15))

        # 中文语言包状态
        chi_sim_status = "已安装" if status["language_chi_sim"] else "未安装"
        tk.Label(
            status_frame,
            text=f"{tesseract_config['tesseract']['files']['language_chi_sim']['icon']} 中文语言包",
            bg='#2D2D2D', fg='white',
            font=('Arial', 11)
        ).pack(anchor=tk.W)

        tk.Label(
            status_frame,
            text=f"   {chi_sim_status} ({tesseract_config['files']['language_chi_sim']['size']})",
            bg='#2D2D2D', fg='#9E9E9E',
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=(0, 15))

        # 英文语言包状态
        eng_status = "已安装" if status["language_eng"] else "未安装"
        tk.Label(
            status_frame,
            text=f"{tesseract_config['files']['language_eng']['icon']} 英文语言包",
            bg='#2D2D2D', fg='white',
            font=('Arial', 11)
        ).pack(anchor=tk.W)

        tk.Label(
            status_frame,
            text=f"   {eng_status} ({tesseract_config['files']['language_eng']['size']})",
            bg='#2D2D2D', fg='#9E9E9E',
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=(0, 15))

        # 按钮区域
        button_frame = tk.Frame(main_frame, bg='#2D2D2D')
        button_frame.pack(fill=tk.X, pady=(20, 0))

        if not all(status.values()):
            # 有缺失依赖，显示安装按钮
            install_button = tk.Button(
                button_frame,
                text="📥 安装缺失的依赖",
                bg='#4CAF50',
                fg='white',
                font=('Arial', 11, 'bold'),
                command=lambda: self.show_download_dialog(downloader),
                relief=tk.FLAT,
                height=40
            )
            install_button.pack(fill=tk.X, padx=10, pady=5)

            skip_button = tk.Button(
                button_frame,
                text="⏭️ 跳过（可能导致功能异常）",
                bg='#F44336',
                fg='white',
                font=('Arial', 10),
                command=lambda: self.skip_install(install_callback),
                relief=tk.FLAT
            )
            skip_button.pack(fill=tk.X, padx=10, pady=5)
        else:
            # 所有依赖已安装
            tk.Label(
                button_frame,
                text="✅ 所有依赖已安装",
                bg='#4CAF50',
                fg='white',
                font=('Arial', 12, 'bold'),
                height=2
            ).pack(fill=tk.X, padx=10, pady=10)

            continue_button = tk.Button(
                button_frame,
                text="继续启动程序",
                bg='#2196F3',
                fg='white',
                font=('Arial', 10, 'bold'),
                command=lambda: self.continue_launch(install_callback),
                relief=tk.FLAT
            )
            continue_button.pack(fill=tk.X, padx=10, pady=10)

        self.root.mainloop()

    def show_download_dialog(self, downloader: DependencyDownloader):
        """显示下载对话框"""
        # 关闭当前窗口
        self.root.destroy()

        # 创建下载窗口
        download_window = tk.Tk()
        download_window.title("VocabGo RPA - 下载依赖")
        download_window.geometry("500x300")
        download_window.configure(bg='#2D2D2D')
        download_window.attributes('-topmost', True)

        main_frame = tk.Frame(download_window, bg='#2D2D2D', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        tk.Label(
            main_frame,
            text="📥 正在下载依赖...",
            bg='#2D2D2D',
            fg='#4FC3F7',
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 20))

        # 状态显示
        self.status_var = tk.StringVar(value="准备下载...")
        status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            bg='#2D2D2D',
            fg='white',
            font=('Arial', 11)
        )
        status_label.pack(pady=(0, 10))

        # 详细信息
        self.detail_var = tk.StringVar(value="")
        detail_label = tk.Label(
            main_frame,
            textvariable=self.detail_var,
            bg='#2D2D2D',
            fg='#FFA726',
            font=('Arial', 9)
        )
        detail_label.pack(pady=(0, 5))

        # 进度条
        progress_frame = tk.Frame(main_frame, bg='#2D2D2D')
        progress_frame.pack(fill=tk.X, pady=(10, 0))

        self.progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        progress_bar.pack()

        # 文件大小信息
        self.total_var = tk.StringVar(value="0 MB / 0 MB")
        total_label = tk.Label(
            progress_frame,
            textvariable=self.total_var,
            bg='#2D2D2D',
            fg='#9E9E9E',
            font=('Arial', 9)
        )
        total_label.pack(pady=(5, 0))

        # 取消按钮
        cancel_button = tk.Button(
            main_frame,
            text="❌ 取消",
            bg='#9E9E9E',
            fg='white',
            font=('Arial', 10),
            command=lambda: self.cancel_download(download_window, downloader),
            relief=tk.FLAT
        )
        cancel_button.pack(pady=(20, 0))

        # 定义进度回调
        def progress_callback(current, total, filename, percent):
            self.status_var.set(f"正在下载: {filename}")
            self.detail_var.set(f"进度: {percent:.1f}%")
            self.progress_var.set(percent)
            self.total_var.set(f"{current // (1024*1024)} MB / {total // (1024*1024)} MB")
            download_window.update()

        # 在新线程中执行下载
        def download_thread():
            success = downloader.install_all_dependencies(progress_callback)
            if success:
                download_window.destroy()
                messagebox.showinfo("成功", "所有依赖安装完成！")
            else:
                download_window.destroy()
                messagebox.showerror("失败", "依赖安装失败，请检查网络连接和错误信息。")

        import threading
        threading.Thread(target=download_thread, daemon=True).start()

        download_window.mainloop()

    def cancel_download(self, window, downloader):
        """取消下载"""
        downloader.cancel_download()
        window.destroy()
        messagebox.showinfo("已取消", "下载已取消，程序可能无法正常工作。")

    def skip_install(self, install_callback: Callable[[], None]):
        """跳过安装"""
        self.root.destroy()
        install_callback()

    def continue_launch(self, install_callback: Callable[[], None]):
        """继续启动程序"""
        self.root.destroy()
        install_callback()


def check_and_install_dependencies(install_callback: Callable[[], None]):
    """
    检查并安装依赖

    Args:
        install_callback: 安装完成后的回调函数
    """
    if GUI_AVAILABLE:
        # 使用GUI界面
        gui = DependencyInstallerGUI()
        gui.show_dependency_check(install_callback)
    else:
        # 使用命令行界面
        print("正在检查依赖...")
        downloader = DependencyDownloader()
        status = downloader.check_dependencies()

        print("\n当前依赖状态:")
        for dep, installed in status.items():
            icon = "✓" if installed else "✗"
            print(f"  {icon} {dep}")

        if not all(status.values()):
            print("\n开始安装缺失的依赖...")
            downloader.install_all_dependencies()
        else:
            print("\n所有依赖已安装！")

        install_callback()


def get_dependency_info() -> dict:
    """获取依赖信息（用于打包脚本）"""
    downloader = DependencyDownloader()
    status = downloader.check_dependencies()

    tesseract_config = DEPENDENCIES["tesseract"]

    # 计算需要下载的文件和大小
    missing_files = []
    total_size = 0

    for dep, installed in status.items():
        if not installed and dep in tesseract_config["files"]:
            file_info = tesseract_config["files"][dep]
            missing_files.append(file_info)
            if "size" in file_info:
                total_size += int(file_info["size"].replace(" MB", ""))

    return {
        "all_installed": all(status.values()),
        "missing_files": missing_files,
        "total_size_mb": total_size,
        "install_dir": str(downloader.install_dir)
    }


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk, messagebox

    print("VocabGo RPA 依赖管理器")
    print("=" * 50)

    # 测试依赖检查
    info = get_dependency_info()

    print("\n依赖信息:")
    print(f"  全部安装: {info['all_installed']}")
    print(f"  缺失文件数: {len(info['missing_files'])}")
    print(f"  需要下载: ~{info['total_size_mb']} MB")
    print(f"  安装目录: {info['install_dir']}")

    # 如果有GUI，显示界面
    if GUI_AVAILABLE:
        def empty_callback():
            print("启动主程序...")
            sys.exit(0)

        check_and_install_dependencies(empty_callback)
    else:
        print("命令行模式完成")