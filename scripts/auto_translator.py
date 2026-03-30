#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动听音翻译机 - VocabGo RPA 系统
功能：静默监听 VB-CABLE 虚拟声卡 -> 自动切分音频 -> 云端识别 -> LLM 翻译 -> 终端打印
使用 sounddevice 替代 pyaudio
"""

import sounddevice as sd
import soundfile as sf
import requests
import json
import threading
import sys
import os
import numpy as np
import tempfile
import time
from pathlib import Path

# 添加项目根目录到路径，以便导入配置
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ================= 配置区 =================
# 从配置文件加载 LLM 设置
CONFIG_FILE = project_root / "config" / "qwen-config.json"

def load_config():
    """加载 API 配置"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("❌ [配置文件未找到]: 请确保 qwen-config.json 存在于 config/ 目录下")
        return None
    except json.JSONDecodeError:
        print("❌ [配置文件格式错误]: 请检查 qwen-config.json 的格式")
        return None

config = load_config()
if not config:
    sys.exit(1)

# 从配置文件中获取 API 设置
LLM_API_URL = config.get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
LLM_API_KEY = config.get("api_key", "")
LLM_MODEL = config.get("model", "qwen-plus")

# 百度语音识别 API 配置
BAI_DU_API_KEY = config.get("baidu_api_key", "")
BAI_DU_SECRET_KEY = config.get("baidu_secret_key", "")
# ==========================================

# 录音参数
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.1  # 100ms
SILENCE_THRESHOLD = 0.02  # 静音阈值
SILENCE_DURATION = 1.0  # 静音持续时间（秒）
MAX_DURATION = 5.0  # 最大录音时长（秒）

class AudioRecorder:
    """使用 sounddevice 的音频录制器"""

    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.silence_start = None
        self.start_time = None

    def callback(self, indata, frames, time_info, status):
        """音频流回调函数"""
        if status:
            print(f"⚠️ 音频流状态: {status}")

        # 计算当前音量
        volume = np.max(np.abs(indata))

        if volume > SILENCE_THRESHOLD:
            # 有声音
            if self.recording:
                self.audio_data.extend(indata.tolist())
            elif self.start_time is None:
                # 开始录音
                self.recording = True
                self.audio_data.extend(indata.tolist())
                self.start_time = time.time()
            self.silence_start = None
        else:
            # 静音
            if self.recording and self.silence_start is None:
                self.silence_start = time.time()
            elif self.recording and self.silence_start and (time.time() - self.silence_start) > SILENCE_DURATION:
                # 静音持续超过阈值，停止录音
                self.recording = False

    def record_until_silence(self):
        """录音直到静音"""
        print("🎤 [正在录音...]")
        self.audio_data = []
        self.silence_start = None
        self.start_time = None
        self.recording = False

        with sd.InputStream(callback=self.callback,
                         channels=CHANNELS,
                         samplerate=SAMPLE_RATE):
            while True:
                if not self.recording and len(self.audio_data) > 0:
                    # 录音结束
                    print("✅ [录音完成]")
                    break

                if len(self.audio_data) > SAMPLE_RATE * MAX_DURATION * CHANNELS:
                    # 超过最大时长，强制停止
                    print("⏱️ [达到最大录音时长]")
                    break

                time.sleep(0.01)

        # 转换为 numpy 数组
        if self.audio_data:
            return np.array(self.audio_data, dtype=np.float32)
        return None

class AutoTranslator:
    def __init__(self):
        self.is_running = True
        self.processing_count = 0
        self.bearer_token = None

    def get_baidu_token(self):
        """获取百度 API Token"""
        if self.bearer_token:
            return self.bearer_token

        if not BAI_DU_API_KEY or not BAI_DU_SECRET_KEY:
            print("❌ [百度 API Key 未配置]")
            return None

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": BAI_DU_API_KEY,
            "client_secret": BAI_DU_SECRET_KEY
        }

        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()
            self.bearer_token = response.json()['access_token']
            return self.bearer_token
        except Exception as e:
            print(f"❌ [获取百度 Token 失败]: {e}")
            return None

    def recognize_baidu(self, audio_data):
        """使用百度语音识别 API"""
        token = self.get_baidu_token()
        if not token:
            return None

        # 保存音频到临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
            sf.write(f, audio_data, SAMPLE_RATE)

        try:
            url = "https://vop.baidu.com/server_api"
            params = {
                "dev_pid": 1737,  # 英语模型
                "token": token,
                "format": "wav",
                "rate": 16000,
                "cuid": "vocabgo_rpa_001"  # 设备唯一标识
            }

            with open(temp_file, 'rb') as f:
                audio_data_bytes = f.read()

            headers = {
                'Content-Type': 'audio/wav; rate=16000',
                'Content-Length': str(len(audio_data_bytes))
            }

            response = requests.post(url, params=params, headers=headers, data=audio_data_bytes, timeout=10)
            response.raise_for_status()

            result = response.json()

            if result.get('err_no') == 0:
                return result.get('result', [''])[0]
            else:
                print(f"❌ [百度识别错误] 错误码: {result.get('err_no')}, 信息: {result.get('err_msg', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"❌ [百度识别失败]: {e}")
            return None
        finally:
            # 删除临时文件
            try:
                os.remove(temp_file)
            except:
                pass

    def translate_with_llm(self, english_text):
        """调用大模型 API 进行翻译"""
        if not LLM_API_KEY or LLM_API_KEY.startswith("YOUR_API_KEY"):
            return "⚠️ [请先配置 API Key]"

        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }

        # 使用配置文件中的听力翻译 prompt
        system_prompt = config.get("prompts", {}).get("listening", {}).get(
            "system",
            "你是一个极速翻译引擎。请直接给出英文单词或短语的中文意思，不要解释，不要标点。"
        )

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": english_text}
            ],
            "temperature": config.get("temperature", 0.1),
            "max_tokens": config.get("max_tokens", 100)
        }

        try:
            response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()

            # 兼容不同 API 响应格式
            if "choices" in result:
                return result['choices'][0]['message']['content'].strip()
            elif "output" in result:  # 通义千问格式
                return result['output']['text'].strip()
            else:
                return f"❌ [未知响应格式]: {result}"

        except requests.exceptions.Timeout:
            return "⚠️ [翻译请求超时]"
        except requests.exceptions.RequestException as e:
            return f"❌ [API 请求失败]: {e}"
        except (KeyError, IndexError) as e:
            return f"❌ [响应解析错误]: {e}"

    def process_audio(self, audio_data, attempt=1):
        """后台处理音频：识别 + 翻译"""
        try:
            self.processing_count += 1
            print(f"\n🔄 [音频 #{self.processing_count}] 正在识别...")

            # 使用百度语音识别
            english_text = self.recognize_baidu(audio_data)

            if not english_text:
                raise ValueError("识别结果为空")

            # 打印识别出的英文
            print(f"🇺🇸 听到的英文: \033[1;33m{english_text}\033[0m")

            # 调用大模型翻译
            print("🧠 [正在请求 LLM 翻译...]")
            chinese_meaning = self.translate_with_llm(english_text)

            # 打印最终结果
            print(f"🇨🇳 中文翻译: \033[1;32m{chinese_meaning}\033[0m")
            print("-" * 60)

        except ValueError as e:
            print(f"🔇 [音频 #{self.processing_count}] {e}")
            print("-" * 60)
        except Exception as e:
            print(f"⚠️ 处理异常: {e}")
            print("-" * 60)

    def list_devices(self):
        """列出所有可用的音频设备"""
        print("=" * 60)
        print("🎤 检测到的音频设备:")
        print("=" * 60)
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            device_type = "🎤 输入" if device['max_input_channels'] > 0 else "🔊 输出"
            channels = device['max_input_channels'] if device['max_input_channels'] > 0 else device['max_output_channels']
            print(f"  [{i:2d}] {device_type:6s} {device['name'][:50]:50s} ({channels}ch)")

        # 找到默认输入设备
        default_input = sd.default.device[0]
        print("=" * 60)
        print(f"💡 当前默认输入设备: [{default_input}] {devices[default_input]['name']}")
        print("=" * 60)

    def test_microphone(self):
        """测试麦克风设备"""
        print("\n🧪 [麦克风测试] 请说话...")

        try:
            print("📡 正在校准环境底噪，请保持安静 2 秒钟...")

            # 录制 2 秒静音进行校准
            duration = 2.0
            recording = sd.rec(int(duration * SAMPLE_RATE),
                             samplerate=SAMPLE_RATE,
                             channels=CHANNELS)
            sd.wait()

            print("✅ 环境底噪校准完成")
            print("🔊 正在监听测试... (5秒后自动结束)")

            # 录制 5 秒测试音频
            duration = 5.0
            recording = sd.rec(int(duration * SAMPLE_RATE),
                             samplerate=SAMPLE_RATE,
                             channels=CHANNELS)
            sd.wait()

            print("✅ 测试录音完成！")
            print("💡 如果没有报错，说明设备连接正常")

            # 可选：播放录制的音频
            play = input("是否播放测试录音？(Y/n): ").strip().lower()
            if play != 'n':
                sd.play(recording, SAMPLE_RATE)
                sd.wait()

            return True

        except Exception as e:
            print(f"❌ 麦克风测试失败: {e}")
            return False

    def test_recognition(self):
        """测试语音识别"""
        print("\n🧪 [语音识别测试] 请说一个英语单词...")

        try:
            recorder = AudioRecorder()
            print("🎤 开始录音... (说完后等待 1 秒)")
            audio_data = recorder.record_until_silence()

            if audio_data is not None:
                print("🔄 正在识别...")
                result = self.recognize_baidu(audio_data)

                if result:
                    print(f"✅ 识别结果: {result}")
                    print("🧠 正在翻译...")
                    translation = self.translate_with_llm(result)
                    print(f"✅ 翻译结果: {translation}")
                    return True
                else:
                    print("❌ 识别失败")
                    return False
            else:
                print("❌ 没有录到音频")
                return False

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False

    def start(self):
        """启动自动翻译"""
        self.list_devices()

        # 询问是否进行麦克风测试
        test_choice = input("\n是否进行麦克风测试？(Y/n): ").strip().lower()
        if test_choice != 'n':
            if not self.test_microphone():
                print("❌ 麦克风测试失败，请检查 VB-CABLE 配置")
                return

        # 询问是否测试语音识别
        recognition_test = input("\n是否测试语音识别？(Y/n): ").strip().lower()
        if recognition_test != 'n':
            self.test_recognition()

        print("\n" + "=" * 60)
        print("🎧 全自动听音翻译机 已启动")
        print("=" * 60)
        print("📝 操作说明:")
        print("  1. 确保微信网页中的音频正在播放")
        print("  2. 脚本会自动捕获音频、识别、翻译")
        print("  3. 按 Ctrl+C 可随时停止")
        print("=" * 60)

        recorder = AudioRecorder()

        # 死循环：一直监听
        while self.is_running:
            try:
                print("⏸️ [等待音频...]")
                audio_data = recorder.record_until_silence()

                if audio_data is not None:
                    # 不阻塞下一次录音，开线程处理
                    threading.Thread(target=self.process_audio, args=(audio_data,), daemon=True).start()

            except KeyboardInterrupt:
                print("\n\n🛑 已手动停止程序。")
                break
            except Exception as e:
                print(f"⚠️ 监听发生异常: {e}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="VocabGo 全自动听音翻译机")
    parser.add_argument("--list", action="store_true", help="列出所有可用的音频设备")
    parser.add_argument("--test", action="store_true", help="测试当前麦克风设备")
    parser.add_argument("--test-recognition", action="store_true", help="测试语音识别功能")
    parser.add_argument("--check-api", action="store_true", help="检查 API 配置")

    args = parser.parse_args()

    translator = AutoTranslator()

    if args.list:
        translator.list_devices()
    elif args.test:
        translator.test_microphone()
    elif args.test_recognition:
        translator.test_recognition()
    elif args.check_api:
        print("🔍 [API 配置检查]")
        print(f"  LLM API URL: {LLM_API_URL}")
        print(f"  LLM Model: {LLM_MODEL}")
        print(f"  LLM API Key: {'✅ 已配置' if LLM_API_KEY and not LLM_API_KEY.startswith('YOUR_API_KEY') else '❌ 未配置'}")
        print(f"  百度 API Key: {'✅ 已配置' if BAI_DU_API_KEY else '❌ 未配置'}")
        print(f"  百度 Secret Key: {'✅ 已配置' if BAI_DU_SECRET_KEY else '❌ 未配置'}")
    else:
        translator.start()

if __name__ == "__main__":
    main()
