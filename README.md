# VocabGo RPA - 大学英语线上作业半自动化辅助系统

## 项目简介

这是一个基于 Windows 10 环境的 **OS 级 RPA（机器人流程自动化）** 辅助系统，专为词达人（app.vocabgo.com）等大学英语线上作业设计。

### 核心理念

- **非侵入性**：不修改网页代码，不拦截网络封包，不触发教务系统的前端检测脚本
- **跨环境兼容**：利用 PC 版微信内置浏览器解决"仅限微信打开"的限制
- **模块化解耦**：将"听、看、想、显"四个环节交给最专业的工具处理

### 技术架构

**方案一：完整工具链**
```
PC微信载体
    ↓
Translumo（视觉感知） + CapsWriter-Offline（听觉感知）
    ↓
通义千问API（逻辑大脑）
    ↓
人工操作提交
```

**方案二：轻量级自动翻译机（推荐）**
```
PC微信载体 + VB-CABLE虚拟声卡
    ↓
自动听音翻译机（Python脚本）
    ↓
通义千问API（逻辑大脑）
    ↓
人工操作提交
```

**方案三：一体化 GUI 翻译助手（最新）** ⭐
```
PC微信载体
    ↓
一体化 GUI（语音识别 + OCR + 翻译）
    ↓
通义千问API（逻辑大脑）
    ↓
人工操作提交
```

**推荐理由**：
- 🎨 更易用：单一窗口，操作简单
- 🚀 更轻量：无需安装大型本地模型
- 💻 对低配电脑更友好：CPU 占用 < 1%
- 🎯 更自动化：零点击，静默监听
- 🆓 成本更低：完全使用云端 API

---

## 系统要求

- 操作系统：Windows 10（版本 2004 或更高）或 Windows 11
- 内存：至少 4 GB RAM
- 存储：至少 2 GB 可用空间
- 网络：稳定互联网连接（用于通义千问 API）
- 其他：PC 版微信

---

## 快速开始

### 1. 工具安装

**方案一：完整工具链**
#### Translumo OCR 工具
- **文档**：`docs/01-translumo-installation.md`
- **下载脚本**：`scripts/download_translumo.ps1`
- **功能**：实时屏幕 OCR 识别和翻译

#### CapsWriter-Offline 录音工具
- **文档**：`docs/02-capswriter-installation.md`
- **下载脚本**：`scripts/download_capswriter.ps1`
- **功能**：系统内录音和语音转文字

**方案二：轻量级自动翻译机（推荐）**
#### 自动听音翻译机
- **文档**：`docs/05-auto-translator-setup.md`
- **Python脚本**：`scripts/auto_translator.py`
- **功能**：VB-CABLE 静默监听 + 云端识别 + LLM 翻译

**方案三：一体化 GUI 翻译助手（最新）** ⭐
#### VocabGo 翻译助手 GUI
- **文档**：`docs/06-gui-setup.md`
- **Python脚本**：`scripts/translator_gui.py`
- **启动脚本**：`scripts/start_gui.bat`
- **功能**：
  - 语音识别（题型2：听力选择）
  - OCR 识别（题型1：画线翻译，使用百度 OCR API）
  - 自动翻译（通义千问 API）
  - 一体化 GUI（类似 Translumo）
  - 支持区域选择和快捷键

#### 通义千问 API
- **文档**：`docs/03-qwen-api-configuration.md`
- **配置文件**：`config/qwen-config.json`
- **辅助脚本**：`scripts/qwen_helper.py`
- **功能**：智能语义分析和翻译

### 2. 配置步骤

**方案一：完整工具链配置**
1. **下载并解压工具**
   ```bash
   cd vocabgo-rpa/scripts
   powershell -ExecutionPolicy Bypass -File download_translumo.ps1
   powershell -ExecutionPolicy Bypass -File download_capswriter.ps1
   ```

2. **配置通义千问 API**
   - 获取 API Key（见文档 03）
   - 编辑 `config/qwen-config.json`
   - 测试连接：`python scripts/qwen_helper.py test`

3. **启动工具**
   - 启动 Translumo：`tools/Translumo/Translumo.exe`
   - 启动 CapsWriter：`tools/CapsWriter-Offline/start_client.exe`

**方案二：自动翻译机配置（推荐）**
1. **安装 VB-CABLE 虚拟声卡**
   - 下载：https://vb-audio.com/Cable/
   - 安装驱动并重启电脑
   - 在 Windows 声音设置中将 VB-CABLE 设为默认设备

2. **安装 Python 依赖**
   ```bash
   pip install SpeechRecognition pyaudio requests
   ```

3. **配置通义千问 API**
   - 获取 API Key（见文档 03）
   - 编辑 `config/qwen-config.json`

4. **启动自动翻译机**
   ```bash
   python scripts/auto_translator.py
   ```

**方案三：一体化 GUI 配置（最新，推荐）** ⭐
1. **安装 Python 依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置通义千问 API**
   - 获取 API Key（见文档 03）
   - 编辑 `config/qwen-config.json`

3. **启动 GUI**
   ```bash
   cd scripts
   start_gui.bat
   ```

4. **使用 OCR 功能（可选）**
   ```bash
   pip install winrt keyboard Pillow
   ```

5. **配置语音识别 API**
   - 阿里云语音识别（推荐）：见文档 `docs/07-aliyun-speech-setup.md`
   - 百度语音识别：需要在设置中配置 API Key

6. **使用 OCR 功能**
   - 点击"🖼️ OCR"按钮打开 OCR 窗口
   - 点击"📐 选择区域"框选屏幕文字
   - 按 `~` 键触发 OCR 识别
   - 详见文档 `docs/08-ocr-integration.md`

### 3. 使用流程

#### 题型1：画线单词翻译题
**方法一：使用 Translumo**
1. 按 `Alt + Q` 选择题目区域
2. 按 `~` 开始 OCR 识别
3. 查看 Translumo 显示的翻译结果
4. 在词达人中选择正确答案

**方法二：使用 GUI OCR（推荐）** ⭐
1. 点击 GUI 中的"🖼️ OCR"按钮
2. 点击"📐 选择区域"，用鼠标框选题目文字
3. 按 `~` 键触发 OCR 识别
4. 自动显示识别结果和中文翻译
5. 在词达人中选择正确答案

#### 题型2：听力音频汉语选择题

**方法一：使用 CapsWriter（完整工具链）**
1. 确认 CapsWriter 系统录音已启用
2. 在词达人中播放音频
3. 查看字幕条显示的识别结果
4. 根据识别的英文单词选择中文选项

**方法二：使用自动翻译机（推荐，轻量级）**
1. 启动自动翻译机脚本
2. 脚本会静默监听 VB-CABLE 虚拟声卡
3. 在词达人中点击播放音频
4. **音频自动流经虚拟线缆，脚本自动识别并翻译**
5. 终端直接显示英文和中文翻译
6. 根据翻译结果选择答案

**方法三：使用 GUI 语音识别（最新，推荐）** ⭐
1. 启动 GUI（`start_gui.bat`）
2. GUI 会自动开始语音监听（无需额外配置）
3. 在词达人中点击播放音频
4. **自动识别并翻译，结果显示在 GUI 中**
5. 根据翻译结果选择答案

**方法四：使用 GUI OCR（最新，推荐）** ⭐⭐
1. 启动 GUI（`start_gui.bat`）
2. 点击"🖼️ OCR"按钮打开 OCR 窗口
3. 点击"📐 选择区域"，用鼠标框选题目文字
4. 按 `~` 键触发 OCR 识别
5. 使用百度 OCR API 进行文字识别
6. 自动显示识别结果和中文翻译
7. 根据翻译结果选择答案

**三种方法对比：**

| 特性 | CapsWriter | 自动翻译机 | GUI 语音识别 | GUI OCR |
|------|-----------|-----------|-------------|----------|
| 硬件要求 | 较高 | 较低 | 较低 | 较低 |
| CPU 占用 | 中等（本地模型） | 极低（< 1%） | 极低（< 1%） | 极低（< 1%） |
| 操作方式 | 显示字幕窗口 | 终端彩色输出 | GUI 界面 | GUI 界面 |
| 自动化程度 | 需要配置 | 零点击自动化 | 零点击自动化 | 需要选择区域 |
| 推荐度 | 适合高端电脑 | **适合所有电脑** | **适合所有电脑** | **适合所有电脑** |

---

## 项目结构

```
vocabgo-rpa/
├── config/                 # 配置文件
│   └── qwen-config.json  # 通义千问配置
├── docs/                  # 文档
│   ├── 01-translumo-installation.md
│   ├── 02-capswriter-installation.md
│   ├── 03-qwen-api-configuration.md
│   ├── 04-complete-usage-guide.md
│   ├── 05-auto-translator-setup.md
│   ├── 06-gui-setup.md
│   ├── 07-aliyun-speech-setup.md
│   └── 08-ocr-integration.md
├── scripts/               # 脚本
│   ├── download_translumo.ps1
│   ├── download_capswriter.ps1
│   ├── auto_translator.py
│   ├── translator_gui.py  # GUI 翻译助手
│   ├── start_gui.bat      # 启动 GUI 脚本
│   ├── qwen_helper.py
│   ├── prompt_optimizer.py
│   ├── quick_launch.bat
│   └── startup.bat
├── tools/                # 工具（需要下载）
│   ├── Translumo/
│   └── CapsWriter-Offline/
└── README.md            # 本文件
```

---

## 主要工具

### 1. VocabGo 翻译助手 GUI（最新推荐）⭐

**功能**：
- 语音识别（题型2：听力选择）
- OCR 识别（题型1：画线翻译）
- 区域选择和快捷键触发（类似 Translumo）
- 自动翻译（通义千问 API）
- 一体化 GUI 界面

**启动方式**：
```bash
cd scripts
start_gui.bat
```

**特性**：
- 🎨 暗色主题，界面美观
- 🎯 置顶窗口，不遮挡内容
- 🔄 自动监听，零点击操作
- 📐 区域选择，灵活识别
- ⌨️ 快捷键支持（`~` 键）
- 🎚️ 透明度调节
- ⚙️ 完整设置界面
- ☁️ 百度 OCR API（云端，无需本地模型）

**使用方式**：
1. **语音识别**：启动后自动开始，播放音频即可
2. **OCR 识别**：点击"🖼️ OCR"按钮，选择区域，按 `~` 键识别

### 2. 自动听音翻译机（推荐）

**功能**：
- 静默监听 VB-CABLE 虚拟声卡
- Google Web Speech API 识别（免费）
- 通义千问 API 翻译
- 彩色终端输出
- 零点击自动化

**启动方式**：
```bash
python scripts/auto_translator.py
```

**高级选项**：
```bash
# 列出所有可用麦克风
python scripts/auto_translator.py --list

# 测试当前麦克风
python scripts/auto_translator.py --test

# 检查 API 配置
python scripts/auto_translator.py --check-api
```

**配置要求**：
- VB-CABLE 虚拟声卡（免费）
- Python 依赖：SpeechRecognition, pyaudio, requests
- 通义千问 API Key

**优势**：
- 超轻量：无需本地模型
- 对低配电脑友好：CPU 占用 < 1%
- 完全自动化：静默监听，自动触发

### 2. Translumo - 屏幕 OCR 和翻译

**功能**：
- 实时 OCR 识别
- 多 OCR 引擎支持
- 实时翻译和显示

**快捷键**：
- `Alt + G`：打开设置
- `Alt + Q`：选择屏幕区域
- `~`：开始/停止翻译

**推荐配置**：
- OCR 引擎：Windows OCR（仅启用）
- 识别语言：English
- 翻译语言：Chinese (Simplified)

### 3. CapsWriter-Offline - 系统录音和语音识别

**功能**：
- 系统内录音（Loopback）
- 实时语音转文字
- 字幕显示

**基本操作**：
- `Caps Lock`：按住录音，松开停止
- 自动显示识别结果

**关键配置**：
- ✅ 勾选"录制系统声音 (Loopback)"
- 识别语言：English
- 字幕位置：屏幕顶部

### 3. 通义千问 API - 智能语义分析

**功能**：
- 上下文感知翻译
- 重点单词识别
- 选项对比分析

**使用方式**：
- 集成到 Translumo（推荐）
- 独立脚本调用
- 通过 CapsWriter LLM 角色

---

## 使用指南详解

### 准备阶段

1. **窗口布局**
   - 左侧 2/3 屏幕：PC 微信（作业窗口）
   - 右侧 1/3 屏幕：工具窗口

2. **工具初始化**
   - 启动 Translumo，设置 OCR 区域
   - 启动 CapsWriter，启用系统录音
   - 配置通义千问 API

### 作业流程

#### 文字题处理
```
遇到题目 → 等待 OCR 识别 → 查看翻译结果 → 选择答案 → 下一题
```

#### 听力题处理
```
点击播放 → 观看字幕 → 识别单词 → 选择中文选项 → 下一题
```

---

## 安全建议

### 反检测措施

1. **控制答题节奏**
   - ✅ 每题至少停留 5-8 秒
   - ✅ 模拟正常学习速度
   - ❌ 避免秒杀式答题

2. **模拟自然操作**
   - ✅ 鼠标点击不总是正中心
   - ✅ 稍微偏离模拟人类操作
   - ✅ 真实阅读题目

3. **分批作业**
   - ✅ 做 20 题休息几分钟
   - ❌ 避免一次性刷完 200 题
   - ✅ 避开高峰时段

4. **数据安全**
   - ✅ 妥善保管 API Key
   - ✅ 使用环境变量存储
   - ❌ 不要分享 API Key

---

## 常见问题

### Q: Translumo 无法识别文字
**A**:
1. 检查 OCR 区域设置
2. 确保窗口处于活动状态
3. 检查屏幕缩放比例（建议 100%）
4. 尝试重启 Translumo

### Q: CapsWriter 无法录音系统声音
**A**:
1. 确认勾选了"录制系统声音 (Loopback)"
2. 检查音频输出设备选择
3. 确认微信浏览器有声音输出
4. 检查系统音频驱动

### Q: 通义千问 API 调用失败
**A**:
1. 检查 API Key 是否正确
2. 确认账户有足够配额
3. 检查网络连接
4. 查看错误详情（见文档 03）

### Q: 整体响应速度慢
**A**:
1. 只启用 Windows OCR 引擎
2. 最小化捕获区域
3. 使用 qwen-turbo 模型
4. 关闭不必要的程序

---

## 成本估算

### 工具成本
- Translumo：免费开源
- CapsWriter-Offline：免费开源
- 通义千问 API：按量付费（新用户有免费额度）

### Token 消耗
- 每次翻译：50-100 tokens
- 每次语义分析：100-200 tokens
- 通义千问价格：qwen-plus 约 ¥0.004/千tokens

### 估算
- 100 道题：约 10,000-20,000 tokens
- 成本：约 ¥0.04-0.08
- 可以先使用免费额度测试

---

## 性能优化

### 提高识别准确率
- ✅ 最小化 OCR 区域
- ✅ 确保网络稳定
- ✅ 使用高质量翻译服务
- ✅ 优化 Prompt 设计

### 提高响应速度
- ✅ 只使用 Windows OCR
- ✅ 减小捕获区域
- ✅ 使用 SSD 存储
- ✅ 关闭后台程序

---

## 进阶技巧

### 1. 快捷键自定义
- Translumo：设置中修改
- CapsWriter：修改 `config_client.py`

### 2. 多区域同时识别
- 设置主区域（题目）
- 设置次区域（选项）
- 同时识别获取完整上下文

### 3. Prompt 优化
- 提供清晰的上下文
- 使用示例提高准确率
- 根据题型定制 Prompt

### 4. 自动化批处理
- 编写脚本自动切换区域
- 结合快捷键实现流程自动化
- 创建题库缓存提高效率

---

## 下一步

### 配置完成后的优化
1. 调试各工具配置
2. 测试不同题型的处理效果
3. 优化 Prompt 和显示设置
4. 建立个人使用习惯

### 深度学习
- 阅读 Translumo 源码学习 OCR
- 研究 CapsWriter 模型原理
- 探索通义千问 API 高级用法

---

## 技术支持

### 文档目录
1. [Translumo 安装配置指南](docs/01-translumo-installation.md)
2. [CapsWriter-Offline 安装配置指南](docs/02-capswriter-installation.md)
3. [通义千问 API 配置指南](docs/03-qwen-api-configuration.md)
4. [完整使用指南](docs/04-complete-usage-guide.md)
5. [自动听音翻译机 - 完整安装配置指南](docs/05-auto-translator-setup.md) ⭐
6. [GUI 翻译助手 - 一体化界面使用指南](docs/06-gui-setup.md) ⭐⭐
7. [阿里云语音识别配置指南](docs/07-aliyun-speech-setup.md)
8. [OCR 功能使用指南（类似 Translumo，使用百度 OCR API）](docs/08-ocr-integration.md) ⭐

### 工具官方资源
- Translumo：https://github.com/ramjke/Translumo
- CapsWriter-Offline：https://github.com/HaujetZhao/CapsWriter-Offline
- 通义千问：https://tongyi.aliyun.com/

### 常用命令
```bash
# 下载工具
cd scripts
powershell -ExecutionPolicy Bypass -File download_translumo.ps1
powershell -ExecutionPolicy Bypass -File download_capswriter.ps1

# 测试通义千问 API
python qwen_helper.py test

# 翻译测试
python qwen_helper.py translate "The quick brown fox jumps over the lazy dog."

# 翻译单词测试
python qwen_helper.py word "beautiful"

# 启动 GUI 翻译助手（最新）
cd scripts
start_gui.bat
```

---

## 免责声明

本系统仅供学习和研究使用，请遵守相关法律法规和平台使用规则。

使用本系统进行作业辅助时，请注意：
- 合理使用，不要过度依赖
- 以学习为主要目的
- 遵守学术诚信原则
- 承担使用风险和责任

---

## 更新日志

### v3.0.0 (2026-03-30)
- 🎉 新增一体化 GUI 翻译助手
- ✅ 集成语音识别（题型2：听力选择）
- ✅ 集成 OCR 识别（题型1：画线翻译，使用百度 OCR API）
- ✅ 类似 Translumo 的区域选择功能
- ✅ 全局快捷键支持（`~` 键触发）
- ✅ 自动翻译（通义千问 API）
- ✅ 暗色主题，界面美观
- ✅ 置顶窗口，透明度调节
- ✅ 完整设置界面
- ✅ 支持阿里云和百度语音识别
- ✅ 支持百度 OCR API（云端，无需本地模型）

### v2.0.0 (2026-03-30)
- 🎉 新增自动听音翻译机
- ✅ 支持 VB-CABLE 虚拟声卡静默监听
- ✅ 零点击自动化体验
- ✅ 超轻量设计，CPU 占用 < 1%
- ✅ 完整的安装配置文档
- ✅ 改进的快速启动菜单
- ✅ 支持多种 LLM API（通义千问、DeepSeek 等）

### v1.0.0 (2026-03-29)
- 初始版本发布
- 集成 Translumo OCR
- 集成 CapsWriter-Offline 录音
- 集成通义千问 API
- 完整配置文档

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## 许可证

MIT License

---

**🎉 开始你的大学英语学习辅助之旅吧！**