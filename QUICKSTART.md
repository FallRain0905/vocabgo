# 快速启动指南 - 自动听音翻译机

## 5 分钟快速上手

### 第 1 步：安装 VB-CABLE (2 分钟)

1. 下载 VB-CABLE：https://vb-audio.com/Cable/
2. 解压后以管理员身份运行 `VBCABLE_Setup.exe`
3. 重启电脑

### 第 2 步：配置系统音频 (1 分钟)

**设置默认播放设备：**
- 打开 Windows 声音设置
- 找到 "CABLE Input" 并设为默认输出设备

**设置默认录音设备：**
- 在声音设置中找到 "CABLE Output (VB-Audio Virtual Cable)"
- 将其设为默认输入设备

### 第 3 步：安装 Python 依赖 (1 分钟)

打开命令行运行：

```bash
pip install SpeechRecognition
pip install pipwin
pipwin install pyaudio
pip install requests
```

### 第 4 步：配置 API Key (1 分钟)

1. 访问 https://dashscope.aliyuncs.com/ 注册账号
2. 获取 API Key
3. 编辑 `config/qwen-config.json`，填入你的 API Key

### 第 5 步：启动并使用 (1 分钟)

```bash
python scripts/auto_translator.py
```

**开始答题：**
1. 脚本会自动校准环境噪音
2. 在微信网页中点击播放听力音频
3. **音频自动流经虚拟线缆，脚本自动识别并翻译**
4. 终端显示：
```
🇺🇸 听到的英文: beautiful
🇨🇳 中文翻译: 美丽的
```

---

## 常见问题快速解决

### 问题：脚本无法访问麦克风

**解决：**
```bash
# 1. 检查设备列表
python scripts/auto_translator.py --list

# 2. 测试麦克风
python scripts/auto_translator.py --test
```

### 问题：识别失败

**解决：**
- 确认 VB-CABLE 已设为默认输入设备
- 检查网络连接（需要访问 Google）
- 调高音频播放音量

### 问题：API 翻译失败

**解决：**
```bash
# 检查 API 配置
python scripts/auto_translator.py --check-api
```

确保 `config/qwen-config.json` 中的 API Key 正确。

---

## 快捷参考

```bash
# 启动自动翻译机
python scripts/auto_translator.py

# 使用快速启动菜单
cd scripts
quick_launch.bat
# 选择 [4] Auto Translator

# 列出可用设备
python scripts/auto_translator.py --list

# 测试麦克风
python scripts/auto_translator.py --test

# 检查 API
python scripts/auto_translator.py --check-api
```

---

## 下一步

详细配置请查看：[自动听音翻译机完整指南](docs/05-auto-translator-setup.md)
