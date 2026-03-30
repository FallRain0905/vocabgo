"""
通义千问 Prompt 优化器
根据词达人不同题型，生成优化的 Prompt
"""

import json
from pathlib import Path

class PromptOptimizer:
    def __init__(self, config_path=None):
        """初始化 Prompt 优化器"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "qwen-config.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.prompts = self.config.get('prompts', {})

    def get_translation_prompt(self, sentence, options=None, word_context=True):
        """
        生成翻译题的优化 Prompt

        Args:
            sentence: 英文句子
            options: 选项列表 ["A. xxx", "B. xxx", ...]
            word_context: 是否需要强调单词语境

        Returns:
            优化后的 Prompt
        """
        base_prompt = self.prompts.get('translation', {}).get('base_prompt',
            "You are an English expert. Please analyze the following English sentence.")

        if word_context:
            prompt = f"""{base_prompt}

Sentence: {sentence}

Tasks:
1. Identify the emphasized word (usually underlined or highlighted).
2. Analyze the context of the entire sentence.
3. Provide the Chinese meaning of this word in the current context.
"""

            if options:
                prompt += f"4. Compare with the following options and recommend the best choice:\n"
                for i, option in enumerate(options, 1):
                    prompt += f"   {chr(64 + i)}. {option}\n"

            prompt += """
Please respond in Chinese with this exact format:
【重点单词】：[the emphasized word]
【语境含义】：[Chinese meaning in context]
【最佳答案】：[A/B/C/D]
【解释】：[brief explanation why this is the best answer]

Note: Focus on the context-appropriate meaning, not just dictionary definitions.
"""
        else:
            prompt = f"""{base_prompt}

Sentence: {sentence}

Please provide an accurate Chinese translation that considers the context.
Use clear, natural Chinese suitable for language learning.
"""

        return prompt

    def get_listening_prompt(self, word, options=None, context="vocabulary learning"):
        """
        生成听力题的优化 Prompt

        Args:
            word: 听力中识别的英文单词或短语
            options: 选项列表
            context: 使用场景描述

        Returns:
            优化后的 Prompt
        """
        base_prompt = self.prompts.get('listening', {}).get('base_prompt',
            "You are an English expert. Please analyze the English word/phrase from listening.")

        prompt = f"""{base_prompt}

Context: This is from an English {context} exercise.

Word/Phrase: {word}

Tasks:
1. Provide the most accurate Chinese translation.
"""

        if options:
            prompt += f"2. Match the English word with the best Chinese option:\n"
            for i, option in enumerate(options, 1):
                prompt += f"   {chr(64 + i)}. {option}\n"

        prompt += """
Please respond in Chinese with this exact format:
【中文含义】：[accurate translation]
【最佳答案】：[A/B/C/D]

Note: Consider the common usage in English learning materials.
"""

        return prompt

    def get_advanced_analysis_prompt(self, sentence, highlighted_word, options):
        """
        生成高级分析 Prompt（用于复杂语境）

        Args:
            sentence: 完整句子
            highlighted_word: 强调/画线的单词
            options: 选项列表

        Returns:
            高级分析 Prompt
        """
        prompt = f"""You are an expert English professor specializing in vocabulary learning and context analysis.

Complete Sentence: {sentence}

Highlighted/Underlined Word: {highlighted_word}

Options:
{self._format_options(options)}

Tasks:
1. Analyze the grammatical function of the highlighted word in this sentence.
2. Determine its meaning based on the surrounding context.
3. Compare the options and identify which one matches the contextual meaning best.
4. Provide reasoning for your choice.

Please respond in Chinese with this format:
【单词分析】：
- 原形：[base form if applicable]
- 词性：[part of speech]
- 语法功能：[how it functions in the sentence]

【语境含义】：[meaning in this specific context]

【选项分析】：
- A. [evaluation of option A]
- B. [evaluation of option B]
- C. [evaluation of option C]
- D. [evaluation of option D]

【最佳答案】：[A/B/C/D]

【详细解释】：[comprehensive explanation of why this is the best answer]

Note: Consider subtle nuances and how the word is used in this particular sentence structure.
"""
        return prompt

    def get_multi_choice_prompt(self, question, options):
        """
        生成多项选择题 Prompt

        Args:
            question: 问题
            options: 选项列表

        Returns:
            多选题 Prompt
        """
        prompt = f"""You are an English expert. Analyze the following multiple-choice question.

Question: {question}

Options:
{self._format_options(options)}

Tasks:
1. Analyze the question carefully.
2. Evaluate each option.
3. Choose the best answer.

Please respond in Chinese with this format:
【问题理解】：[brief summary of the question]
【最佳答案】：[A/B/C/D]
【解析】：[detailed explanation]
"""
        return prompt

    def get_fill_blank_prompt(self, sentence, blank_word, options):
        """
        生成填空题 Prompt

        Args:
            sentence: 带空格的句子
            blank_word: 要填入的单词
            options: 选项列表

        Returns:
            填空题 Prompt
        """
        prompt = f"""You are an English expert. Analyze this fill-in-the-blank question.

Sentence: {sentence}

Word to fill: {blank_word}

Options:
{self._format_options(options)}

Tasks:
1. Analyze the sentence structure and meaning.
2. Determine which word fits best grammatically and semantically.
3. Choose the best option.

Please respond in Chinese with this format:
【句子分析】：[analysis of sentence structure]
【最佳答案】：[A/B/C/D]
【解释】：[why this word fits best]
"""
        return prompt

    def _format_options(self, options):
        """格式化选项列表"""
        if not options:
            return "No options provided"
        formatted = []
        for i, option in enumerate(options, 1):
            formatted.append(f"{chr(64 + i)}. {option}")
        return "\n".join(formatted)

    def optimize_for_difficulty(self, prompt, difficulty_level="medium"):
        """
        根据难度级别优化 Prompt

        Args:
            prompt: 基础 Prompt
            difficulty_level: "easy", "medium", "hard"

        Returns:
            优化后的 Prompt
        """
        instructions = {
            "easy": "Provide clear, simple explanations suitable for beginners.",
            "medium": "Provide balanced explanations with examples.",
            "hard": "Provide detailed, nuanced explanations with advanced vocabulary insights."
        }

        instruction = instructions.get(difficulty_level, instructions["medium"])

        optimized_prompt = f"""{prompt}

Additional Instruction: {instruction}
"""
        return optimized_prompt

    def add_examples_to_prompt(self, prompt, examples):
        """
        向 Prompt 添加示例

        Args:
            prompt: 基础 Prompt
            examples: 示例列表

        Returns:
            带示例的 Prompt
        """
        example_text = "\n\nExamples:\n"
        for i, example in enumerate(examples, 1):
            example_text += f"\nExample {i}:\n"
            example_text += f"Input: {example['input']}\n"
            example_text += f"Output: {example['output']}\n"

        return f"{prompt}{example_text}"

    def save_custom_prompt(self, prompt_type, prompt_content, filename=None):
        """
        保存自定义 Prompt

        Args:
            prompt_type: "translation", "listening", "custom"
            prompt_content: Prompt 内容
            filename: 自定义文件名
        """
        if filename is None:
            filename = f"{prompt_type}_prompt.txt"

        prompts_dir = Path(__file__).parent.parent / "config" / "custom_prompts"
        prompts_dir.mkdir(exist_ok=True)

        filepath = prompts_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prompt_content)

        return str(filepath)

    def load_custom_prompt(self, filename):
        """
        加载自定义 Prompt

        Args:
            filename: Prompt 文件名

        Returns:
            Prompt 内容
        """
        prompts_dir = Path(__file__).parent.parent / "config" / "custom_prompts"
        filepath = prompts_dir / filename

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()


def main():
    """主函数，用于测试 Prompt 优化器"""
    import sys

    optimizer = PromptOptimizer()

    if len(sys.argv) < 2:
        print("Prompt 优化器使用方法：")
        print("1. 翻译题 Prompt：python prompt_optimizer.py translate '句子' [选项A 选项B 选项C 选项D]")
        print("2. 听力题 Prompt：python prompt_optimizer.py listening '单词' [选项A 选项B 选项C 选项D]")
        print("3. 高级分析 Prompt：python prompt_optimizer.py analyze '句子' '强调词' [选项A 选项B 选项C 选项D]")
        print("4. 保存自定义 Prompt：python prompt_optimizer.py save '类型' '内容' '文件名'")
        print("\n示例：")
        print('python prompt_optimizer.py translate "The quick brown fox." "A. 快速 B. 慢速 C. 棕色 D. 棕毛"')
        return

    command = sys.argv[1]

    if command == "translate" and len(sys.argv) >= 3:
        sentence = sys.argv[2]
        options = sys.argv[3:] if len(sys.argv) > 3 else None
        prompt = optimizer.get_translation_prompt(sentence, options)
        print("\n生成的翻译题 Prompt：")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

    elif command == "listening" and len(sys.argv) >= 3:
        word = sys.argv[2]
        options = sys.argv[3:] if len(sys.argv) > 3 else None
        prompt = optimizer.get_listening_prompt(word, options)
        print("\n生成的听力题 Prompt：")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

    elif command == "analyze" and len(sys.argv) >= 4:
        sentence = sys.argv[2]
        highlighted_word = sys.argv[3]
        options = sys.argv[4:] if len(sys.argv) > 4 else None
        prompt = optimizer.get_advanced_analysis_prompt(sentence, highlighted_word, options)
        print("\n生成的高级分析 Prompt：")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

    elif command == "save" and len(sys.argv) >= 4:
        prompt_type = sys.argv[2]
        content = sys.argv[3]
        filename = sys.argv[4] if len(sys.argv) > 4 else None
        filepath = optimizer.save_custom_prompt(prompt_type, content, filename)
        print(f"✅ Prompt 已保存到: {filepath}")

    else:
        print("❌ 无效的命令参数")
        main()


if __name__ == "__main__":
    main()