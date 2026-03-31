# VocabGo RPA 打包成EXE程序指南

## 概述

将VocabGo RPA打包成可执行文件（.exe），让其他用户无需安装Python环境即可使用。

## 📦 打包方案对比

| 特性 | PyInstaller | cx_Freeze | Nuitka | Briefcase |
|------|-------------|------------|---------|-----------|
| **易用性** | ⭐⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **打包速度** | 中等 | 快 | 慢 | 快 |
| **exe体积** | 大 | 中 | 小 | 大 |
| **性能** | 中 | 中 | 最优 | 中 |
| **跨平台** | 优秀 | 良好 | 优秀 | 最优 |
| **依赖处理** | 强 | 中 | 弱 | 强 |
| **推荐度** | 🌟🌟🌟🌟🌟 | 🌟🌟🌟 | 🌟🌟 | 🌟🌟🌟 |

## 🚀 快速开始（PyInstaller）

### 一键打包

```bash
# 运行打包脚本
cd scripts
python package_exe.py
```

打包脚本会自动：
1. 创建PyInstaller配置文件
2. 安装必要的依赖
3. 执行打包过程
4. 生成可执行文件
5. （可选）创建便携版zip包

### 手动打包

#### 1. 安装PyInstaller

```bash
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 2. 准备图标文件

将图标文件放在 `assets/icon.ico`

**图标要求**：
- 格式：.ico
- 尺寸：包含16x16, 32x32, 48x48, 256x256
- 工具推荐：GIMP, Adobe Photoshop, 在线ico转换器

#### 3. 运行PyInstaller

```bash
cd scripts
pyinstaller translator_gui.py \
    --name=VocabGo_RPA \
    --icon=../assets/icon.ico \
    --windowed \
    --onefile \
    --clean \
    --add-data="../config:config" \
    --add-data="../assets:assets" \
    --add-data="../docs:docs" \
    --hidden-import=tkinter \
    --hidden-import=PIL \
    --hidden-import=mss \
    --hidden-import=sounddevice \
    --hidden-import=keyboard \
    --hidden-import=numpy
```

#### 4. 查看生成的文件

打包完成后，在 `dist/` 目录中找到 `VocabGo_RPA.exe`

## 🎯 PyInstaller参数详解

### 基础参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--name` | 生成的exe名称 | `--name=VocabGo_RPA` |
| `--onefile` | 单文件模式（推荐） | `--onefile` |
| `--windowed` | GUI模式，无控制台 | `--windowed` |
| `--icon` | exe图标文件 | `--icon=../assets/icon.ico` |
| `--clean` | 清理旧的构建文件 | `--clean` |

### 数据文件参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--add-data` | 添加数据文件（源:目标） | `--add-data="../config:config"` |

多个数据文件：
```bash
--add-data="../config:config" \
--add-data="../assets:assets" \
--add-data="../docs:docs"
```

### 隐藏导入参数

| 参数 | 说明 |
|------|------|
| `--hidden-import` | 明确指定的模块会被包含 |
| `--collect-binaries` | 收集二进制依赖 |
| `--collect-data` | 收集数据文件 |

tkinter GUI常用隐藏导入：
```bash
--hidden-import=tkinter \
--hidden-import=tkinter.ttk \
--hidden-import=tkinter.scrolledtext
```

## 📋 高级配置（.spec文件）

### 使用spec文件的优点

1. 更精确的控制打包过程
2. 可以复用配置
3. 支持更复杂的设置
4. 便于版本控制

### spec文件示例

```python
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 项目根目录
project_root = Path(SPECPATH).parent.parent

# 分析阶段
a = Analysis(
    ['scripts/translator_gui.py'],  # 主程序文件
    pathex=[str(project_root)],      # 搜索路径
    binaries=[],                       # 二进制文件
    datas=[                          # 数据文件
        (str(project_root / 'config'), 'config'),
        (str(project_root / 'assets'), 'assets'),
        (str(project_root / 'docs'), 'docs'),
    ],
    hiddenimports=[                    # 隐藏导入
        'tkinter', 'tkinter.ttk',
        'requests', 'json',
        'numpy', 'sounddevice',
        'PIL', 'mss', 'keyboard',
    ],
    hookspath=[],                      # 钩子路径
    hooksconfig={},
    runtime_hooks=[],
    excludes=[                         # 排除的模块
        'matplotlib', 'numpy.testing',
        'unittest', 'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    optimize=0,                       # 优化级别
)

# 可执行文件阶段
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VocabGo_RPA',           # exe名称
    debug=False,                     # 调试模式
    bootloader_ignore_signals=False,
    strip=False,                     # 去除符号
    upx=True,                       # UPX压缩
    console=False,                    # GUI模式
    disable_windowed_traceback=False,
    icon=str(project_root / 'assets' / 'icon.ico'),
)

# 收集阶段
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='VocabGo_RPA',           # 最终目录名
)
```

### 使用spec文件打包

```bash
# 从spec文件打包
pyinstaller vocabgo_rpa.spec

# 清理旧文件
pyinstaller --clean vocabgo_rpa.spec
```

## 🎨 制作图标

### 生成ico文件

#### 方法一：在线转换（推荐）

1. 准备PNG图片（建议1024x1024）
2. 访问：https://icoconvert.com/
3. 上传PNG图片
4. 选择尺寸：16x16, 32x32, 48x48, 64x64, 128x128, 256x256
5. 下载生成的ico文件

#### 方法二：使用GIMP

1. 打开GIMP
2. 导入你的图标图片
3. 图像 → 调整图像大小 → 创建多尺寸
4. 文件 → 导出为 → 选择ICO格式
5. 保存为icon.ico

#### 方法三：使用ImageMagick

```bash
# 安装ImageMagick
choco install imagemagick

# 生成ico文件
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

### 图标建议

- **简洁设计**：避免过多细节
- **高对比度**：在不同背景下清晰可见
- **代表性**：体现VocabGo的特点（翻译、OCR）
- **测试显示**：在不同尺寸下检查效果

## 📦 分发格式

### 格式一：单文件exe

```bash
pyinstaller --onefile translator_gui.py
```

**优势**：
- 用户只需一个exe文件
- 部署简单

**劣势**：
- 启动速度较慢
- 文件体积较大

### 格式二：文件夹模式

```bash
pyinstaller translator_gui.py
```

**优势**：
- 启动速度快
- 文件体积相对小

**劣势**：
- 需要分发整个文件夹
- 用户可能误删文件

### 格式三：便携版zip

```bash
# 1. 正常打包
pyinstaller --onefile translator_gui.py

# 2. 创建zip包（手动或使用打包脚本）
# 包含：VocabGo_RPA.exe + README + 使用说明
```

**便携版优势**：
- 绿色软件，无需安装
- 放在U盘中随处使用
- 清理简单（删除文件夹）

## 🔧 外部依赖处理

### Tesseract处理

VocabGo RPA需要Tesseract，有几种处理方式：

#### 方案一：便携版Tesseract

```bash
# 1. 下载Tesseract便携版
# https://github.com/UB-Mannheim/tesseract/releases

# 2. 解压到项目目录
VocabGo_RPA/
├── VocabGo_RPA.exe
├── tesseract/
│   ├── tesseract.exe
│   └── tessdata/
│       ├── chi_sim.traineddata
│       └── eng.traineddata

# 3. 程序自动查找本地Tesseract
```

**实现方法**：
```python
# 在OCR引擎中添加本地Tesseract查找
def _find_local_tesseract(self):
    # 查找程序目录中的tesseract
    app_dir = Path(__file__).parent
    local_tesseract = app_dir / "tesseract" / "tesseract.exe"
    if local_tesseract.exists():
        return str(local_tesseract)
    # 否则查找系统Tesseract
    return self._find_system_tesseract()
```

#### 方案二：提示用户安装

在首次运行时检查Tesseract：
```python
def check_tesseract(self):
    if not self._tesseract_available():
        msg = ("VocabGo RPA需要Tesseract OCR引擎。\n\n"
                "是否现在打开下载页面？\n"
                "下载地址: https://github.com/UB-Mannheim/tesseract/wiki")
        if messagebox.askyesno("缺少依赖", msg):
            import webbrowser
            webbrowser.open("https://github.com/UB-Mannheim/tesseract/wiki")
```

#### 方案三：自动下载Tesseract

```python
def download_tesseract(self):
    """下载并安装Tesseract到程序目录"""
    import urllib.request
    import zipfile

    # 下载便携版
    url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.0/tesseract-ocr-w64-portable.zip"
    download_path = Path(__file__).parent / "tesseract_portable.zip"

    urllib.request.urlretrieve(url, download_path)

    # 解压
    with zipfile.ZipFile(download_path) as zipf:
        zipf.extractall(Path(__file__).parent)

    # 清理下载文件
    download_path.unlink()
```

### 其他依赖处理

| 依赖 | 处理方式 |
|------|----------|
| **pyaudio** | 提示用户安装或使用sounddevice替代 |
| **numpy** | PyInstaller自动打包 |
| **PIL/Pillow** | PyInstaller自动打包 |
| **mss** | PyInstaller自动打包 |
| **keyboard** | PyInstaller自动打包 |
| **requests** | PyInstaller自动打包 |

## 🧪 减小exe体积

### 方法一：UPX压缩

```bash
# PyInstaller默认使用UPX压缩
# 可以手动调整
pyinstaller --upx-dir=upx_folder translator_gui.py
```

### 方法二：排除不需要的模块

```python
# 在spec文件中添加excludes
excludes=[
    'matplotlib',      # 排除大型库
    'numpy.testing',  # 排除测试模块
    'unittest',       # 排除测试框架
    'pytest',         # 排除测试框架
    'IPython',       # 排除交互式Python
],
```

### 方法三：使用虚拟环境

```bash
# 创建最小虚拟环境
python -m venv venv_lean

# 只安装必要的依赖
venv_lean/Scripts/pip install -r requirements.txt

# 在虚拟环境中打包
venv_lean/Scripts/pyinstaller translator_gui.py
```

### 方法四：Nuitka编译（高级）

```bash
# 安装Nuitka
pip install nuitka

# 编译成exe
python -m nuitka --follow-imports --standalone --output-dir=build translator_gui.py
```

## 📝 安装程序制作（可选）

### 使用NSIS制作安装程序

```nsis
; VocabGo_RPA.nsi
!define APP_NAME "VocabGo RPA"
!define APP_VERSION "3.0.0"

Name "${APP_NAME}"
OutFile "VocabGo_RPA_Setup.exe"
InstallDir "$PROGRAMFILES\VocabGo_RPA"
RequestExecutionLevel admin

Section "Main"
    SetOutPath $INSTDIR

    # 复制主程序
    File /r "dist\VocabGo_RPA\*"

    # 创建桌面快捷方式
    CreateShortCut "$DESKTOP\VocabGo RPA.lnk" "$INSTDIR\VocabGo_RPA.exe"

    # 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\VocabGo RPA"
    CreateShortCut "$SMPROGRAMS\VocabGo RPA\VocabGo RPA.lnk" "$INSTDIR\VocabGo_RPA.exe"

    # 注册表项
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"

    # 创建卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd
```

### 编译NSIS脚本

```bash
# 下载NSIS
choco install nsis

# 编译安装程序
makensis VocabGo_RPA.nsi
```

## 🚀 发布准备

### 版本管理

```bash
# 在脚本中更新版本号
VERSION="3.0.0"
VERSION_DATE=$(date +%Y%m%d)
```

### 生成发布包

```bash
# 1. 打包exe
python scripts/package_exe.py

# 2. 创建便携版zip
python scripts/package_exe.py
# 选择 'y' 创建zip

# 3. 创建安装程序（可选）
makensis VocabGo_RPA.nsi

# 4. 文件结构
dist/
├── VocabGo_RPA/
│   ├── VocabGo_RPA.exe
│   ├── config/
│   ├── assets/
│   └── docs/
├── VocabGo_RPA_v3.0.0_portable.zip
└── VocabGo_RPA_Setup_v3.0.0.exe
```

### 编写发布说明

```markdown
# VocabGo RPA v3.0.0 发布说明

## 下载选项

### 便携版（推荐）
- 文件名：VocabGo_RPA_v3.0.0_portable.zip
- 适合：所有用户
- 优势：绿色软件，无需安装

### 安装版
- 文件名：VocabGo_RPA_Setup_v3.0.0.exe
- 适合：需要桌面快捷方式用户
- 优势：自动创建快捷方式

## 系统要求

- 操作系统：Windows 10/11
- 内存：4GB RAM
- 硬盘：200MB可用空间
- 网络：连接互联网（API调用）

## 新功能

- ✅ 基于NormCap技术的OCR引擎
- ✅ 支持Tesseract OCR
- ✅ 图像预处理优化
- ✅ 详细识别结果（置信度、坐标）

## 使用说明

1. 解压或安装VocabGo RPA
2. 配置通义千问API Key
3. 运行VocabGo_RPA.exe
4. 使用OCR识别和翻译功能

## 常见问题

**Q: 缺少Tesseract**
A: 下载便携版Tesseract，放在程序目录中。

**Q: 杀毒软件误报**
A: 将VocabGo RPA添加到白名单。

## 更新日志

### v3.0.0 (2026-03-31)
- 🎉 全新OCR引擎实现
- ✅ 基于Tesseract命令行
- ✅ 图像预处理优化
- ✅ 详细结果解析
```

### 创建GitHub Release

1. **上传文件**
   - 访问：https://github.com/你的用户名/vocabgo-rpa/releases/new
   - 标题：VocabGo RPA v3.0.0
   - 标签：v3.0.0
   - 描述：复制发布说明内容

2. **上传资源文件**
   - VocabGo_RPA_v3.0.0_portable.zip
   - VocabGo_RPA_Setup_v3.0.0.exe

3. **发布Release**
   - 点击"Publish release"

## 🧪 故障排除

### 打包常见问题

#### 问题1：PyInstaller安装失败

```bash
# 解决方案1：更新pip
python -m pip install --upgrade pip

# 解决方案2：使用国内镜像
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

# 解决方案3：安装到虚拟环境
python -m venv venv
venv/Scripts/pip install pyinstaller
```

#### 问题2：打包后exe无法运行

**症状**：运行exe立即退出或报错

**解决方案**：
1. **在开发环境中测试**
   ```bash
   cd scripts
   python translator_gui.py
   ```

2. **检查依赖是否包含**
   - 查看PyInstaller输出的警告
   - 确保所有依赖都在hiddenimports中

3. **使用控制台模式调试**
   ```bash
   pyinstaller --console translator_gui.py
   ```

4. **检查文件路径**
   - 确保资源文件路径正确
   - 验证config文件包含

#### 问题3：生成的exe太大

**解决方案**：
1. 使用UPX压缩（已默认启用）
2. 排除不必要的模块
3. 使用Nuitka编译（体积更小）
4. 分发文件夹模式而非单文件

#### 问题4：外部依赖问题

**症状**：Tesseract找不到

**解决方案**：
1. **提示用户安装**：在首次运行时检查
2. **打包便携版Tesseract**：与exe一起分发
3. **提供下载链接**：自动跳转到下载页面

## 📊 最佳实践

### 打包前检查清单

- [ ] 代码在开发环境中正常运行
- [ ] 所有依赖都在requirements.txt中
- [ ] 资源文件（配置、图标）准备完成
- [ ] 虚拟环境干净且最小化
- [ ] 测试所有功能正常工作

### 打包后测试清单

- [ ] exe文件能正常启动
- [ ] GUI界面显示正常
- [ ] 语音识别功能正常
- [ ] OCR功能（需要Tesseract）正常
- [ ] 翻译功能正常
- [ ] 配置文件读写正常
- [ ] 快捷键功能正常
- [ ] 错误处理合理
- [ ] 关闭程序时清理资源

### 分发检查清单

- [ ] exe文件大小合理（<50MB单文件，<100MB文件夹）
- [ ] 图标显示正常
- [ ] README和说明文档完整
- [ ] 系统要求明确
- [ ] 安装/解压说明清晰
- [ ] 在干净系统上测试
- [ ] 杀毒软件扫描无威胁

## 🎯 总结

推荐打包方案：

1. **初学者**：使用 `scripts/package_exe.py` 一键打包
2. **高级用户**：创建自定义.spec文件精确控制
3. **专业分发**：使用NSIS制作安装程序
4. **便携版**：推荐便携版zip包发布

核心要点：
- ✅ PyInstaller是最易用的选择
- ✅ spec文件提供精确控制
- ✅ 合理处理Tesseract外部依赖
- ✅ 提供便携版和安装版两种选择
- ✅ 充分测试后再发布

**祝你打包顺利！** 🚀