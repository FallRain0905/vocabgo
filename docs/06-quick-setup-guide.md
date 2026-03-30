# 快速入门指南 - 自动听音翻译机

## ✅ 已完成

- Python 3.14.3 已安装
- VB-CABLE 虚拟声卡已下载
- sounddevice 音频库已安装

## ⚙️ 下一步配置

### 步骤 1：安装 VB-CABLE 驱动

1. 解压 `VBCABLE_Driver_Pack45.zip`
2. 以管理员身份运行 `VBCABLE_Setup64.exe`
3. 安装完成后，**重启电脑**（重要！）

### 步骤 2：配置系统音频

重启后，打开 Windows 设置 → 系统 → 声音

**设置默认播放设备：**
- 选择：`CABLE Input (VB-Audio Virtual Cable)`
- 设置为默认输出设备 ✓

**设置默认录音设备：**
- 选择：`CABLE Output (VB-Audio Virtual Cable)`
- 设置为默认输入设备 ✓

### 步骤 3：申请百度语音识别 API（免费）

**为什么用百度？**
- ✅ 免费额度充足（每秒 5 万次）
- ✅ 支持英语识别
- ✅ API 简单易用

**申请步骤：**

1. 访问百度智能云：https://cloud.baidu.com/

2. 注册/登录账号

3. 进入控制台，搜索"语音识别"或访问：
   https://console.bce.baidu.com/ai/#/ai/speech/overview/index

4. 点击"立即使用" → 创建应用

5. 填写应用信息：
   - 应用名称：随便填，如"VocabGo翻译"
   - 应用类型：选择"其他"
   - 接口选择：勾选"语音识别"

6. 创建成功后，记录下：
   - **API Key**（如：`abcd1234efgh5678`）
   - **Secret Key**（如：`xyz9876mnop4321`）

### 步骤 4：配置通义千问 API（翻译用）

**通义千问费用低，新用户有免费额度：**

1. 访问：https://dashscope.aliyuncs.com/

2. 注册/登录阿里云账号

3. 进入 API-KEY 管理：https://dashscope.console.aliyun.com/apiKey

4. 创建 API-KEY

5. 复制 API Key（格式：`sk-xxxxxxxxxxxxxxxxxxxxxxx`）

### 步骤 5：编辑配置文件

打开文件：
```
c:\Users\surface\OneDrive\Desktop\vocabgo\vocabgo-rpa\config\qwen-config.json
```

修改以下内容：

```json
{
  "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
  "api_key": "sk-你的通义千问API-KEY",  ← 替换这里
  "model": "qwen-plus",
  "temperature": 0.1,
  "max_tokens": 100,
  "baidu_api_key": "你的百度API Key",  ← 替换这里
  "baidu_secret_key": "你的百度Secret Key",  ← 替换这里
  "prompts": {
    ...
  }
}
```

**重要**：
- `api_key`：通义千问的 API Key（用于翻译）
- `baidu_api_key`：百度的 API Key（用于语音识别）
- `baidu_secret_key`：百度的 Secret Key（用于语音识别）

## 🚀 启动测试

### 测试步骤

```bash
cd c:\Users\surface\OneDrive\Desktop\vocabgo\vocabgo-rpa\scripts
python auto_translator.py --check-api
```

你应该看到：
```
🔍 [API 配置检查]
  LLM API URL: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
  LLM Model: qwen-plus
  LLM API Key: ✅ 已配置
  百度 API Key: ✅ 已配置
  百度 Secret Key: ✅ 已配置
```

### 测试麦克风

```bash
python auto_translator.py --test
```

测试音频录制是否正常。

### 测试语音识别

```bash
python auto_translator.py --test-recognition
```

对着麦克风说一个英语单词（如 "apple"），看能否正确识别和翻译。

## 🎧 正式使用

```bash
python auto_translator.py
```

## 📱 完整工作流程

1. **启动脚本**
   ```bash
   python auto_translator.py
   ```

2. **脚本会自动：**
   - 校准环境底噪
   - 列出可用音频设备
   - 进入监听模式

3. **打开微信网页**
   - 在 PC 微信中打开词达人作业
   - 找到听力题目

4. **播放音频**
   - 点击播放按钮
   - 音频会通过 VB-CABLE 路由到脚本
   - 脚本自动识别、翻译
   - 终端立即显示结果

5. **选择答案**
   - 根据显示的中文翻译
   - 在网页中选择正确选项

## 💡 提示

- 确保系统默认播放设备是 `CABLE Input`
- 确保系统默认录音设备是 `CABLE Output`
- 如果识别不准确，可以调大网页音频音量
- 按 `Ctrl+C` 可以随时停止脚本

## ❓ 常见问题

### Q: 百度 API 额度用完了怎么办？
A: 可以申请多个账号，或者使用阿里云语音识别 API（配置稍复杂）

### Q: 识别速度慢怎么办？
A: 检查网络连接，减少 `SILENCE_DURATION` 参数

### Q: 识别准确率低怎么办？
A: 调大网页音量，减少环境噪音

### Q: 通义千问 API 费用高吗？
A: 非常低！1000 次翻译不到 1 毛钱（约 ¥0.3）

## 🎉 开始使用

完成以上配置后，你就可以享受全自动的英语听力翻译了！

遇到问题请查看：`docs/05-auto-translator-setup.md`
