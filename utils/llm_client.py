"""
大模型客户端模块
功能：统一封装豆包大模型的调用，支持文本和JSON两种返回格式
说明：使用requests直接调用API，避免openai SDK的连接池问题
"""

import os
import json
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


class LLMClient:
    """
    大模型客户端类
    使用requests直接调用API，更稳定
    """

    def __init__(self):
        """
        初始化大模型客户端
        """
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model = os.getenv("LLM_MODEL", "doubao-seed-2.1-pro")

        # 最大重试次数
        self.max_retries = 3
        # 每次重试间隔（秒）
        self.retry_delay = 3
        # 请求超时时间（秒）
        self.timeout = 120

        # 构造完整的API端点
        self.api_endpoint = f"{self.base_url}/chat/completions"

        # 请求头
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        if not self.api_key or self.api_key == "你的API密钥":
            print("⚠️  警告：未配置LLM_API_KEY，请在界面中输入或在.env文件中配置")

    def configure(self, api_key: str, base_url: str = None, model: str = None):
        """
        动态配置大模型API参数（用于用户在界面中输入自己的API）

        参数:
            api_key: API密钥
            base_url: API地址（兼容OpenAI格式），不传则保持原有值
            model: 模型名称，不传则保持原有值
        """
        if api_key:
            self.api_key = api_key
        if base_url:
            self.base_url = base_url.rstrip('/')
        if model:
            self.model = model

        # 更新端点和请求头
        self.api_endpoint = f"{self.base_url}/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def is_configured(self) -> bool:
        """
        检查是否已配置有效的API密钥
        """
        return bool(self.api_key) and self.api_key != "你的API密钥"

    def call(self, prompt: str, system_prompt: str = "你是一个专业的助手",
             temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """
        调用大模型，返回纯文本结果

        参数:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词
            temperature: 温度参数，0-1之间
            max_tokens: 最大输出token数

        返回:
            str: 大模型返回的纯文本内容
        """
        # 构造请求体
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        # 重试机制
        for attempt in range(self.max_retries):
            try:
                print(f"⏳ 正在调用大模型（第{attempt + 1}次）...", flush=True)

                # 发送请求
                response = requests.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )

                # 检查HTTP状态码
                if response.status_code != 200:
                    print(f"❌ HTTP错误: {response.status_code}")
                    print(f"响应内容: {response.text[:200]}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise Exception(f"API请求失败: HTTP {response.status_code}")

                # 解析响应
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                print("✅ 调用成功")
                return content

            except requests.exceptions.Timeout:
                print(f"❌ 请求超时（{self.timeout}秒）")
                if attempt < self.max_retries - 1:
                    print(f"⏳ 等待{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"请求超时，已重试{self.max_retries}次")

            except requests.exceptions.ConnectionError as e:
                print(f"❌ 连接错误: {str(e)}")
                if attempt < self.max_retries - 1:
                    print(f"⏳ 等待{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"连接失败，已重试{self.max_retries}次: {str(e)}")

            except Exception as e:
                print(f"❌ 调用失败: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"大模型调用失败，已重试{self.max_retries}次: {str(e)}")

    def call_json(self, prompt: str, system_prompt: str = "你是一个专业的助手",
                  temperature: float = 0.3, max_tokens: int = 4096) -> Dict[str, Any]:
        """
        调用大模型，返回JSON格式结果

        参数:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大输出token数

        返回:
            dict: 解析后的JSON字典
        """
        json_system_prompt = system_prompt + "\n\n重要要求：你必须严格输出合法的JSON格式，不要输出任何其他文字、解释或markdown标记。"

        for attempt in range(self.max_retries):
            try:
                result_text = self.call(
                    prompt=prompt,
                    system_prompt=json_system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # 清理markdown标记
                result_text = result_text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.startswith("```"):
                    result_text = result_text[3:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                result_text = result_text.strip()

                # 解析JSON
                result_dict = json.loads(result_text)
                return result_dict

            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败（第{attempt + 1}次）: {str(e)}")
                print(f"返回的内容是: {result_text[:200]}...")

                if attempt < self.max_retries - 1:
                    print(f"⏳ 等待{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"JSON解析失败，已重试{self.max_retries}次: {str(e)}")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"大模型JSON调用失败: {str(e)}")


# 创建一个全局实例
llm_client = LLMClient()


# 测试代码
