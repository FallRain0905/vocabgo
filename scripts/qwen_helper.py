"""
通义千问 API 辅助脚本
用于词达人翻译题和听力题的 AI 辅助
"""

import requests
import json
import os
from pathlib import Path

class QwenHelper:
    def __init__(self, config_path=None):
        """初始化通义千问助手"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "qwen-config.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.api_endpoint = self.config['qwen_api']['api_endpoint']
        self.api_key = self.config['qwen_api']['api_key']
        self.model = self.config['qwen_api']['model']
        self.temperature = self.config['qwen_api']['temperature']
        self.max_tokens = self.config['qwen_api']['max_tokens']

        # 从环境变量读取 API Key（优先级高于配置文件）
        env_key = os.environ.get('QWEN_API_KEY')
        if env_key:
            self.api_key = env_key

    def _call_api(self, prompt):
        """调用通义千问 API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an English expert specializing in language learning."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            response = requests.post(self.api_endpoint, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return f"API调用错误: {e}"
        except KeyError:
            return "API返回格式错误"

    def translate_sentence(self, sentence, options=None):
        """
        翻译句子并分析重点单词

        Args:
            sentence: 英文句子
            options: 选项列表，如 ["A. 选项1", "B. 选项2", ...]

        Returns:
            翻译和分析结果
        """
        prompt = f"""You are an English expert. Please analyze the following English sentence:

{sentence}

Task:
1. Identify the emphasized word (usually underlined or highlighted).
2. Provide the Chinese meaning of this word in the current context.
"""

        if options:
            prompt += f"3. Compare with these options and give the best answer:\n"
            for i, option in enumerate(options, 1):
                prompt += f"   {chr(64 + i)}. {option}\n"

        prompt += """
Please respond in Chinese with this format:
【重点单词】：[word]
【语境含义】：[Chinese meaning]
【最佳答案】：[A/B/C/D]
【解释】：[brief explanation]
"""

        return self._call_api(prompt)

    def translate_listening_word(self, word, options=None):
        """
        翻译听力中的单词

        Args:
            word: 英文单词或短语
            options: 选项列表

        Returns:
            翻译结果
        """
        prompt = f"""You are an English expert. Please translate the following English word from listening:

{word}

Task:
1. Provide the most accurate Chinese translation.
2. If there are options, match with the best one.
"""

        if options:
            prompt += f"\nOptions:\n"
            for i, option in enumerate(options, 1):
                prompt += f"{chr(64 + i)}. {option}\n"

        prompt += """
Please respond in Chinese with this format:
【中文含义】：[meaning]
【最佳答案】：[A/B/C/D]
"""

        return self._call_api(prompt)

    def simple_translate(self, text):
        """
        简单翻译

        Args:
            text: 要翻译的文本

        Returns:
            翻译结果
        """
        prompt = f"""Please translate the following English text to Chinese:

{text}

Provide the most accurate translation suitable for language learning context."""

        return self._call_api(prompt)

    def test_connection(self):
        """测试 API 连接"""
        prompt = "Hello, this is a test. Please reply with 'Connection successful'."
        result = self._call_api(prompt)
        print("API 连接测试：")
        print(result)
        return "Connection successful" in result.lower()


def main():
    """主函数，用于测试"""
    import sys

    # 创建助手实例
    helper = QwenHelper()

    # 测试连接
    if not helper.test_connection():
        print("❌ API 连接失败，请检查配置")
        return

    print("✅ API 连接成功\n")

    # 根据命令行参数执行不同功能
    if len(sys.argv) < 2:
        print("使用方法：")
        print("1. 测试连接：python qwen_helper.py test")
        print("2. 翻译句子：python qwen_helper.py translate '句子'")
        print("3. 翻译单词：python qwen_helper.py word '单词'")
        print("\n示例：")
        print('python qwen_helper.py translate "The quick brown fox jumps over the lazy dog."')
        return

    command = sys.argv[1]

    if command == "test":
        # 已在上面测试
        pass

    elif command == "translate" and len(sys.argv) >= 3:
        sentence = ' '.join(sys.argv[2:])
        result = helper.translate_sentence(sentence)
        print("\n翻译结果：")
        print(result)

    elif command == "word" and len(sys.argv) >= 3:
        word = ' '.join(sys.argv[2:])
        result = helper.translate_listening_word(word)
        print("\n翻译结果：")
        print(result)

    else:
        print("❌ 无效的命令参数")
        main()


if __name__ == "__main__":
    main()