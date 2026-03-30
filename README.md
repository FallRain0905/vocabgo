# VocabGo RPA - 大学英语线上作业半自动化辅助系统

## 项目简介

这是一个基于 Windows 10 环境的 **OS 级 RPA（机器人流程自动化）** 辅助系统，专为词达人（app.vocabgo.com）等大学英语线上作业设计。

### 核心理念

- **非侵入性**：不修改网页代码，不拦截网络封包，不触发教务系统的前端检测脚本
- **跨环境兼容**：利用 PC 版微信内置浏览器解决"仅限微信打开"的限制
- **模块化解耦**：将"听、想、显"三个环节交给最专业的工具处理

### 技术架构

**方案一：轻量级自动翻译机（推荐）**
```
PC微信载体 + VB-CABLE虚拟声卡
    ↓
自动听音翻译机（Python脚本）
    ↓
通义千问API（逻辑大脑）
    ↓
人工操作提交
```

**方案二：一体化 GUI 翻译助手（最新）** ⭐
```
PC微信载体
    ↓
一体化 GUI（语音识别 + 自动翻译）
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

**方案一：轻量级自动翻译机（推荐）**
#### 自动听音翻译机
- **文档**：`docs/05-auto-translator-setup.md`
- **Python脚本**：`scripts/auto_translator.py`
- **功能**：VB-CABLE 静默监听 + 云端识别 + LLM 翻译

**方案二：一体化 GUI 翻译助手（最新）** ⭐
#### VocabGo 翻译助手 GUI
- **文档**：`docs/06-gui-setup.md`
- **Python脚本**：`scripts/translator_gui.py`
- **启动脚本**：`scripts/start_gui.bat`
- **功能**：
  - 语音识别（题型2：听力选择）
  - 自动翻译（通义千问 API）
  - 一体化 GUI 界面
  - 暗色主题，置顶窗口

#### 通义千问 API
- **文档**：`docs/03-qwen-api-configuration.md`
- **配置文件**：`config/qwen-config.json`
- **辅助脚本**：`scripts/qwen_helper.py`
- **功能**：智能语义分析和翻译

### 2. 配置步骤

**方案一：自动翻译机配置（推荐）**
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

**方案二：一体化 GUI 配置（最新，推荐）** ⭐
1. **安装 Python 依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置通义千问 API**
   - 获取 API Key（见文档 03）
   - 编辑 `config/qwen-config.json`

3. **配置语音识别 API**
   - 阿里云语音识别（推荐）：见文档 `docs/07-aliyun-speech-setup.md`

4. **启动 GUI**
   ```bash
   cd scripts
   start_gui.bat
   ```

### 3. 使用流程

#### 题型2：听力音频汉语选择题

**方法一：使用自动翻译机（推荐，轻量级）**
1. 启动自动翻译机脚本
2. 脚本会静默监听 VB-CABLE 虚拟声卡
3. 在词达人中点击播放音频
4. **音频自动流经虚拟线缆，脚本自动识别并翻译**
5. 终端直接显示英文和中文翻译
6. 根据翻译结果选择答案

**方法二：使用 GUI 语音识别（最新，推荐）** ⭐
1. 启动 GUI（`start_gui.bat`）
2. GUI 会自动开始语音监听（无需额外配置）
3. 在词达人中点击播放音频
4. **自动识别并翻译，结果显示在 GUI 中**
5. 根据翻译结果选择答案

**两种方法对比：**

| 特性 | 自动翻译机 | GUI 语音识别 |
|------|-----------|-------------|
| 硬件要求 | 较低 | 较低 |
| CPU 占用 | 极低（< 1%） | 极低（< 1%） |
| 操作方式 | 终端彩色输出 | GUI 界面 |
| 自动化程度 | 零点击自动化 | 零点击自动化 |
| 推荐度 | **适合所有电脑** | **适合所有电脑** |

---

## 项目结构

```
vocabgo-rpa/
├── config/                 # 配置文件
│   └── qwen-config.json  # 通义千问配置
├── docs/                  # 文档
│   ├── 03-qwen-api-configuration.md
│   ├── 05-auto-translator-setup.md
│   ├── 06-gui-setup.md
│   └── 07-aliyun-speech-setup.md
├── scripts/               # 脚本
│   ├── auto_translator.py
│   ├── translator_gui.py  # GUI 翻译助手
│   ├── start_gui.bat      # 启动 GUI 脚本
│   ├── qwen_helper.py
│   ├── prompt_optimizer.py
│   ├── quick_launch.bat
│   └── startup.bat
└── README.md            # 本文件
```

---

## 主要工具

### 1. VocabGo 翻译助手 GUI（最新推荐）⭐

**功能**：
- 语音识别（题型2：听力选择）
- 自动翻译（通义千问 API）
- 一体化 GUI 界面
- 暗色主题，界面美观
- 置顶窗口，不遮挡内容
- 自动监听，零点击操作
- 透明度调节
- 完整设置界面

**启动方式**：
```bash
cd scripts
start_gui.bat
```

**使用方式**：
启动后自动开始语音监听，播放音频即可

### 2. 自动听音翻译机（推荐）

**功能**：
- 静默监听 VB-CABLE 虚拟声卡
- 阿里云语音识别 API
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

---

## 使用指南详解

### 准备阶段

1. **窗口布局**
   - 左侧 2/3 屏幕：PC 微信（作业窗口）
   - 右侧 1/3 屏幕：工具窗口

2. **工具初始化**
   - 启动 GUI 或自动翻译机
   - 启用语音监听
   - 配置通义千问 API

### 作业流程

#### 听力题处理
```
点击播放 → 观看识别结果 → 查看翻译 → 选择中文选项 → 下一题
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

### Q: 语音识别失败
**A**:
1. 检查麦克风是否正确配置
2. 确认语音识别 API 密钥是否正确
3. 检查网络连接
4. 确认音频输出设备选择正确

### Q: 通义千问 API 调用失败
**A**:
1. 检查 API Key 是否正确
2. 确认账户有足够配额
3. 检查网络连接
4. 查看错误详情（见文档 03）

### Q: 整体响应速度慢
**A**:
1. 使用 qwen-turbo 模型
2. 关闭不必要的程序
3. 确保网络稳定

---

## 成本估算

### 工具成本
- 通义千问 API：按量付费（新用户有免费额度）

### Token 消耗
- 每次翻译：50-100 tokens
- 通义千问价格：qwen-plus 约 ¥0.004/千tokens

### 估算
- 100 道题：约 5,000-10,000 tokens
- 成本：约 ¥0.02-0.04
- 可以先使用免费额度测试

---

## 性能优化

### 提高识别准确率
- ✅ 确保网络稳定
- ✅ 使用高质量语音识别服务
- ✅ 优化 Prompt 设计

### 提高响应速度
- ✅ 使用 qwen-turbo 模型
- ✅ 关闭后台程序
- ✅ 使用 SSD 存储

---

## 进阶技巧

### 1. Prompt 优化
- 提供清晰的上下文
- 使用示例提高准确率
- 根据题型定制 Prompt

### 2. 自动化批处理
- 创建题库缓存提高效率
- 结合快捷键实现流程自动化

---

## 下一步

### 配置完成后的优化
1. 调试各工具配置
2. 测试不同题型的处理效果
3. 优化 Prompt 和显示设置
4. 建立个人使用习惯

### 深度学习
- 探索通义千问 API 高级用法

---

## 技术支持

### 文档目录
1. [通义千问 API 配置指南](docs/03-qwen-api-configuration.md)
2. [自动听音翻译机 - 完整安装配置指南](docs/05-auto-translator-setup.md) ⭐
3. [GUI 翻译助手 - 一体化界面使用指南](docs/06-gui-setup.md) ⭐⭐
4. [阿里云语音识别配置指南](docs/07-aliyun-speech-setup.md)

### 工具官方资源
- 通义千问：https://tongyi.aliyun.com/

### 常用命令
```bash
# 测试通义千问 API
python scripts/qwen_helper.py test

# 翻译测试
python scripts/qwen_helper.py translate "The quick brown fox jumps over the lazy dog."

# 翻译单词测试
python scripts/qwen_helper.py word "beautiful"

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

### v2.0.0 (2026-03-30)
- 🎉 移除 OCR 功能，专注于语音识别
- ✅ 优化 GUI 界面
- ✅ 简化配置流程
- ✅ 改进语音识别集成

### v1.0.0 (2026-03-29)
- 初始版本发布
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
