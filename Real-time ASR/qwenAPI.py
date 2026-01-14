import os
from typing import Optional, List, Dict, Any
import dashscope
from dashscope import Generation

class QwenAPI:
    """
    封装 Qwen 大模型 API 调用的工具类。
    支持通过用户输入获取模型回答。
    """

    def __init__(
        self,
        model: str = "qwen-max",
        api_key: Optional[str] = None,
        temperature: float = 0.85,
        top_p: float = 0.9,
        max_tokens: int = 2048
    ):
        """
        初始化 Qwen API 客户端。

        :param model: 使用的 Qwen 模型名称，如 'qwen-max', 'qwen-plus', 'qwen-turbo' 等。
        :param api_key: DashScope API Key。若未提供，则从环境变量 DASHSCOPE_API_KEY 读取。
        :param temperature: 生成文本的随机性（0～1），值越大越随机。
        :param top_p: 核采样参数，控制生成多样性。
        :param max_tokens: 最大生成 token 数。
        """
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        # 设置 API Key
        if api_key:
            dashscope.api_key = api_key
        else:
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
            if not dashscope.api_key:
                raise ValueError("未提供 API Key，请通过参数或环境变量 DASHSCOPE_API_KEY 设置。")

    def ask(self, user_input: str, system_prompt: Optional[str] = None) -> str:
        """
        向 Qwen 模型提问并返回回答。

        :param user_input: 用户的问题或输入内容。
        :param system_prompt: 可选的系统提示（用于设定角色或行为准则）。
        :return: 模型生成的回答文本。
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        try:
            response = Generation.call(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                result_format="message"
            )
            if response.status_code == 200:
                return response.output.choices[0].message.content.strip()
            else:
                raise RuntimeError(f"API 调用失败: {response.code} - {response.message}")
        except Exception as e:
            raise RuntimeError(f"调用 Qwen API 时发生错误: {e}")

    def chat(self, conversation: List[Dict[str, str]]) -> str:
        """
        支持多轮对话（传入完整对话历史）。

        :param conversation: 对话历史列表，格式如：
            [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！有什么我可以帮你的吗？"},
                {"role": "user", "content": "今天天气怎么样？"}
            ]
        :return: 模型生成的回答。
        """
        try:
            response = Generation.call(
                model=self.model,
                messages=conversation,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                result_format="message"
            )
            if response.status_code == 200:
                return response.output.choices[0].message.content.strip()
            else:
                raise RuntimeError(f"API 调用失败: {response.code} - {response.message}")
        except Exception as e:
            raise RuntimeError(f"调用 Qwen API 时发生错误: {e}")

if __name__ == '__main__':
    # 方式1：使用环境变量中的 API Key
    qwen = QwenAPI(model="qwen-max",api_key="")

    # 带系统提示
    answer = qwen.ask(
        "写一首关于春天的诗。",
        system_prompt="你是一位浪漫主义诗人，语言优美，富有意境。"
    )
    print("诗歌：", answer)