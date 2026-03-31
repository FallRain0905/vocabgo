# OCR功能配置指南

## 概述

VocabGo RPA v3.0 新增了强大的OCR（光学字符识别）功能，支持处理纯文本阅读题、选词填空题等多种题型。本文档详细介绍OCR功能的安装、配置和使用方法。

## 技术方案对比

### 方案一：Windows原生OCR（推荐）

**优势：**
- ✅ 极致轻量：CPU占用<1%
- ✅ 极速识别：<100ms响应时间
- ✅ 完全离线：无需网络连接
- ✅ 系统集成：直接使用Windows 10/11内置能力
- ✅ 坐标精准：提供字符级边界框坐标

**劣势：**
- ⚠️ 需要Visual Studio编译环境安装winsdk
- ⚠️ 仅支持Windows 10/11系统

### 方案二：Tesseract OCR（备用）

**优势：**
- ✅ 开源免费
- ✅ 跨平台支持
- ✅ 支持多语言
- ✅ 安装相对简单

**劣势：**
- ⚠️ 需要单独安装可执行文件
- ⚠️ 识别速度稍慢
- ⚠️ 准确率略低于Windows原生OCR

## 安装配置

### Windows原生OCR安装

#### 1. 安装Visual Studio（如果未安装）

下载并安装Visual Studio Community（免费）：
- 下载地址：https://visualstudio.microsoft.com/downloads/
- 安装时选择"使用C++的桌面开发"工作负载
- 确保包含MSVC编译器和Windows SDK

#### 2. 安装Python依赖

```bash
# 使用清华镜像加速下载
pip install winsdk mss pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 验证安装

```bash
python scripts/ocr_engine.py
```

如果看到"SUCCESS: Windows OCR engine initialized"消息，说明安装成功。

### Tesseract OCR安装

#### 1. 下载Tesseract

- 下载地址：https://github.com/UB-Mannheim/tesseract/wiki
- 选择最新版本（推荐tesseract-ocr-w64-setup）
- 运行安装程序

#### 2. 配置安装

- 安装路径：`C:\Program Files\Tesseract-OCR\`（默认路径）
- 勾选"中文简体语言包"
- 完成安装

#### 3. 安装Python依赖

```bash
pip install pytesseract mss pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 4. 验证安装

```bash
# 检查Tesseract是否安装成功
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version

# 检查Python绑定
python -c "import pytesseract; print('Tesseract Python绑定正常')"
```

## GUI配置

### 启动GUI

```bash
cd scripts
start_gui.bat
```

### OCR设置

1. **打开设置窗口**
   - 点击GUI中的"⚙️ 设置"按钮

2. **配置OCR参数**
   - **启用OCR功能**：勾选"启用OCR功能"复选框
   - **快捷键设置**：设置截图识别快捷键（默认F8）
     - 支持单键：如`f8`、`f9`
     - 支持组合键：如`ctrl+alt+o`、`shift+f8`
   - **识别区域设置**：（可选，提高准确性）
     - 上边距：截图区域上边界距离屏幕顶部的像素值
     - 左边距：截图区域左边界距离屏幕左侧的像素值
     - 宽度：截图区域的宽度
     - 高度：截图区域的高度
     - *留空则识别整个屏幕*

3. **保存设置**
   - 点击"💾 保存"按钮
   - 重启GUI使设置生效

## 使用方法

### 基本操作

1. **准备题目**
   - 将英语题目显示在屏幕上
   - 确保文字清晰可见
   - 避免标题栏、菜单栏干扰

2. **截图识别**
   - 方法一：按`F8`快捷键
   - 方法二：点击GUI中的"📷 截图识别"按钮
   - 系统自动进行OCR识别

3. **查看识别结果**
   - 识别的文本显示在"🔍 文本识别"区域
   - 系统自动提取英文单词和中文内容

4. **翻译识别内容**
   - 点击"🧠 翻译识别内容"按钮
   - 系统自动翻译提取的英文内容
   - 翻译结果显示在中文区域

### 高级操作

#### 自定义识别区域

如果识别效果不理想，可以设置特定的识别区域：

1. **确定题目位置**
   - 使用截图工具查看坐标
   - 或者记录大致区域

2. **在设置中配置区域**
   ```
   上边距: 200
   左边距: 100
   宽度: 800
   高度: 400
   ```

3. **测试识别效果**
   - 调整参数直到获得最佳效果

#### 多语言识别

- **中文OCR**：默认使用中文OCR引擎
- **英文OCR**：在代码中切换为英文语言包
- **混合识别**：当前版本优先识别中文，同时提取英文单词

### 操作流程示例

#### 纯文本阅读题处理

```
1. 打开英语阅读题
2. 调整窗口位置，确保题目在识别区域内
3. 按F8进行截图识别
4. 查看识别的英文文本
5. 点击"🧠 翻译识别内容"
6. 根据翻译结果选择答案
```

#### 选词填空题处理

```
1. 打开选词填空题
2. 截图识别整个题目区域
3. 系统自动提取候选词汇
4. 翻译候选词汇了解含义
5. 根据句意和词汇含义选择答案
```

#### 混合题型处理

```
1. 听力题：使用语音识别功能
2. 文本题：使用OCR识别功能
3. 灵活切换两种识别方式
```

## 性能优化

### 提高识别准确率

1. **屏幕设置**
   - 使用100%缩放比例（DPI）
   - 确保文字分辨率足够高
   - 避免屏幕反光或阴影

2. **识别区域**
   - 精确定位题目区域
   - 排除无关界面元素
   - 确保文字完整在区域内

3. **字体和对比度**
   - 使用清晰字体
   - 确保足够的颜色对比度
   - 避免文字重叠或模糊

### 提高响应速度

1. **使用Windows原生OCR**
   - 比Tesseract更快
   - CPU占用更低

2. **减小识别区域**
   - 缩小截图范围
   - 减少识别文字数量

3. **系统优化**
   - 关闭不必要的后台程序
   - 确保系统资源充足

## 常见问题

### Q: winsdk安装失败

**A:**
1. 确保已安装Visual Studio和C++开发工具
2. 检查Windows SDK是否完整安装
3. 或改用Tesseract OCR方案

### Q: Tesseract识别效果不佳

**A:**
1. 确保语言包安装完整
2. 尝试自定义识别区域
3. 检查图像质量和清晰度
4. 或改用Windows原生OCR

### Q: OCR功能按钮灰显不可用

**A:**
1. 检查是否安装了OCR依赖
2. 确认在设置中启用了OCR功能
3. 查看控制台错误信息
4. 重启GUI应用

### Q: 快捷键不工作

**A:**
1. 检查快捷键是否与其他程序冲突
2. 尝试更换快捷键
3. 确保GUI窗口处于活动状态
4. 重新设置并保存

### Q: 识别结果乱码或错误

**A:**
1. 检查系统语言包设置
2. 尝试不同的OCR引擎
3. 调整识别区域
4. 检查源图像文字清晰度

## 故障排除

### 检查OCR引擎状态

```bash
# 测试OCR引擎
python scripts/ocr_engine.py
```

### 检查依赖安装

```bash
# 检查Windows原生OCR
python -c "from scripts.ocr_engine import WINSDK_AVAILABLE; print(WINSDK_AVAILABLE)"

# 检查Tesseract
python -c "from scripts.ocr_engine import TESSERACT_AVAILABLE; print(TESSERACT_AVAILABLE)"
```

### 查看详细日志

启动GUI时，控制台会显示详细的OCR引擎初始化信息：
- `SUCCESS: Windows OCR engine initialized` - Windows原生OCR可用
- `SUCCESS: Using Tesseract OCR engine` - Tesseract OCR可用
- `WARNING: All OCR engines failed` - 所有OCR引擎初始化失败

## 技术支持

如有问题，请检查以下资源：

1. **Windows OCR**：
   - 官方文档：https://docs.microsoft.com/en-us/uwp/api/windows.media.ocr

2. **Tesseract OCR**：
   - 项目主页：https://github.com/tesseract-ocr/tesseract
   - 中文文档：https://tesseract-ocr.github.io/

3. **VocabGo RPA**：
   - 主README：`README.md`
   - 问题反馈：GitHub Issues

## 更新日志

### v3.0.0 (2026-03-31)
- 新增OCR功能
- 支持Windows原生OCR和Tesseract OCR
- 集成快捷键截图识别
- 添加自定义识别区域功能

---

**祝你使用愉快！** 🎉