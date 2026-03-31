# Tesseract OCR 安装配置指南

## 概述

VocabGo RPA v3.0 采用基于NormCap技术的Tesseract OCR方案，相比Windows原生OCR更简单易用，无需复杂的编译环境。

## 为什么选择Tesseract？

| 对比项 | Windows原生OCR | Tesseract OCR |
|-------|--------------|---------------|
| **安装难度** | 困难（需要Visual Studio） | 简单（5分钟搞定） |
| **配置复杂度** | 高 | 低 |
| **依赖环境** | 需要C++编译器 | 只需可执行文件 |
| **识别准确率** | 最优 | 优秀 |
| **跨平台** | 仅Windows | 全平台支持 |
| **安装时间** | 20分钟+ | 5分钟 |

## 快速安装指南

### 方法一：一键安装（推荐）

1. **下载Tesseract安装包**
   ```
   访问：https://github.com/UB-Mannheim/tesseract/wiki
   下载：tesseract-ocr-w64-setup.exe (64位Windows)
   ```

2. **运行安装程序**
   - 双击下载的 `.exe` 文件
   - 点击 "Next" 按照向导完成安装
   - 记住安装路径（默认：`C:\Program Files\Tesseract-OCR\`）

3. **验证安装**
   ```bash
   # 打开命令提示符，运行：
   tesseract --version

   # 应该看到版本信息，例如：
   tesseract 5.3.0
    leptonica-1.83.1
    libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.1.91) : libpng 1.6.39 : libtiff 4.5.1 : zlib 1.2.11 : libwebp 1.3.2
   ```

4. **配置环境变量**（如果自动检测失败）
   - 右键 "此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"用户变量"中：
     - 新建变量 `TESSDATA_PREFIX`，值为Tesseract安装路径（如：`C:\Program Files\Tesseract-OCR`）
     - 编辑变量 `Path`，添加Tesseract路径（如：`C:\Program Files\Tesseract-OCR`）

5. **测试语言包**
   ```bash
   tesseract --list-langs

   # 应该看到：
   List of available languages (1):
   chi_sim
   eng
   ```

### 方法二：便携版安装

1. **下载便携版**
   ```
   访问：https://github.com/UB-Mannheim/tesseract/releases
   下载：tesseract-ocr-w64-portable.zip
   ```

2. **解压到任意目录**
   - 解压到 `D:\Tools\Tesseract-OCR\` 或任意位置

3. **手动设置环境变量**
   - 按方法一的步骤4手动配置环境变量

## Python依赖安装

```bash
# 安装OCR相关依赖
pip install mss numpy pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置文件设置

在 `config/qwen-config.json` 中添加OCR相关配置：

```json
{
  "ocr_enabled": true,
  "ocr_hotkey": "f8",
  "ocr_lang": "chi_sim+eng",
  "ocr_region": {
    "top": 100,
    "left": 100,
    "width": 800,
    "height": 400
  }
}
```

### 配置说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `ocr_enabled` | 是否启用OCR功能 | `true`/`false` |
| `ocr_hotkey` | OCR截图快捷键 | `"f8"`, `"ctrl+alt+o"` |
| `ocr_lang` | OCR识别语言 | `"chi_sim+eng"` 中英文混合 |
| `ocr_region` | 截图区域配置 | 坐标对象，留空则全屏 |

### 常用语言代码

| 语言 | 代码 | 说明 |
|------|------|------|
| 中文简体 | `chi_sim` | 简体中文 |
| 中文繁体 | `chi_tra` | 繁体中文 |
| 英文 | `eng` | 英语 |
| 中英混合 | `chi_sim+eng` | 中英文同时识别（推荐） |

## 使用方法

### 1. 启动GUI

```bash
cd scripts
start_gui.bat
```

### 2. 配置OCR设置

- 点击GUI中的 "⚙️ 设置" 按钮
- 在 "OCR功能设置" 部分：
  - 勾选 "启用OCR功能"
  - 设置快捷键（默认F8）
  - 配置识别语言（推荐 `chi_sim+eng`）
  - 可选：设置识别区域提高准确率

### 3. 进行OCR识别

**方法一：快捷键**
- 按 `F8` 键（或自定义快捷键）
- 系统自动截图并识别

**方法二：GUI按钮**
- 点击 "📷 截图识别" 按钮
- 选择要识别的屏幕区域

### 4. 查看和翻译结果

- 识别结果显示在 "🔍 文本识别" 区域
- 点击 "🧠 翻译识别内容" 进行智能翻译
- 翻译结果显示在 "🇨🇳 中文翻译" 区域

## 故障排除

### 问题1：无法找到Tesseract

**症状：**
```
FileNotFoundError: 无法找到Tesseract可执行文件！
```

**解决方案：**
1. 检查Tesseract是否正确安装
2. 配置 `TESSDATA_PREFIX` 环境变量
3. 或手动指定Tesseract路径

```python
# 在 ocr_engine_v2.py 中修改默认路径
common_paths = [
    r"D:\你的路径\Tesseract-OCR\tesseract.exe",  # 添加你的路径
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    # ...
]
```

### 问题2：识别准确率低

**解决方案：**
1. **优化识别区域**
   - 在设置中配置精确的识别区域
   - 避免无关元素干扰

2. **图像质量检查**
   - 确保屏幕文字清晰可读
   - 使用100% DPI缩放比例
   - 避免屏幕反光或阴影

3. **语言配置优化**
   - 纯英文题目：使用 `eng`
   - 中英混合：使用 `chi_sim+eng`
   - 纯中文：使用 `chi_sim`

### 问题3：识别速度慢

**解决方案：**
1. 缩小识别区域
2. 关闭图像预处理（在OCR引擎中设置）
3. 使用更快的OEM模式

### 问题4：快捷键不工作

**解决方案：**
1. 检查快捷键冲突
2. 尝试更换快捷键
3. 确保GUI窗口处于活动状态
4. 重新设置并保存配置

## 性能优化

### 提高识别准确率

1. **精确识别区域**
   ```
   上边距: 200    # 调整到题目区域顶部
   左边距: 100    # 调整到题目区域左侧
   宽度: 1000     # 覆盖整个题目
   高度: 500      # 包含所有选项
   ```

2. **环境优化**
   - 关闭不必要的程序
   - 使用SSD存储
   - 确保系统资源充足

3. **显示设置**
   - 使用100%缩放比例
   - 清晰显示模式
   - 适当的字体大小

### 提高处理速度

1. **减少识别范围**
   - 只识别题目区域
   - 避免全屏截图

2. **调整OCR参数**
   ```python
   # 在代码中调整参数
   ocr.set_psm(PSM.SINGLE_BLOCK)  # 单一块模式更快
   ocr.set_oem(OEM.TESSERACT_ONLY)  # 仅传统引擎更快
   ```

## 高级配置

### 自定义Tesseract参数

在 `ocr_engine_v2.py` 中可以调整：

```python
# 页面分割模式
class PSM(enum.IntEnum):
    AUTO = 3           # 自动（默认）
    SINGLE_BLOCK = 6   # 单块模式（更快）
    SINGLE_COLUMN = 4  # 单列模式

# OCR引擎模式
class OEM(enum.IntEnum):
    DEFAULT = 3               # 默认（最佳准确率）
    TESSERACT_ONLY = 0       # 仅传统引擎（最快）
    LSTM_ONLY = 1            # 仅LSTM引擎
```

### 图像预处理调整

```python
# 在 _preprocess_image 方法中调整：
resize_factor = 2.0      # 调整放大倍数（1.5-3.0）
padding = 80            # 调整边距大小（50-120）
```

## 测试工具

### 运行OCR测试

```bash
# 测试OCR引擎
python scripts/ocr_engine_v2.py
```

### 运行完整测试

```bash
# 运行完整功能测试
python scripts/test_ocr.py
```

## 常见问题

### Q: Tesseract vs 其他OCR方案？

**A:**
- **Tesseract**：开源免费，准确率优秀，安装简单
- **Windows原生OCR**：系统集成，性能最优，安装复杂
- **在线OCR**：无需本地安装，有网络依赖

对于VocabGo项目，推荐Tesseract方案。

### Q: 需要下载语言包吗？

**A:**
安装程序通常会包含基本语言包（简体中文、英文）。如需其他语言：

1. 下载语言包：`chi_sim.traineddata`
2. 放置到 `C:\Program Files\Tesseract-OCR\tessdata\`
3. 重启应用

### Q: 识别的中文显示为乱码？

**A:**
确保系统编码设置正确，或调整OCR引擎的字符处理逻辑。

## 技术支持

### 获取帮助

1. **文档资源**
   - Tesseract官方：https://tesseract-ocr.github.io/
   - NormCap项目：https://github.com/dynobo/normcap
   - 本项目：README.md

2. **问题反馈**
   - GitHub Issues
   - 查看FAQ文档

### 相关文档

- [OCR功能配置指南](08-ocr-configuration.md)
- [通义千问 API 配置](03-qwen-api-configuration.md)
- [GUI 翻译助手使用](06-gui-setup.md)

## 更新日志

### v3.0.0 (2026-03-31)
- 🎉 采用NormCap技术实现
- ✅ 基于Tesseract命令行
- ✅ 图像预处理优化
- ✅ 详细的OCR结果解析
- ✅ 置信度和坐标信息
- ✅ 灵活的参数配置

---

**祝你使用愉快！** 🎉