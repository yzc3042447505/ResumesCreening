"""
Agent基类模块
功能：所有Agent的父类，封装通用的大模型调用、格式校验、重试逻辑
说明：具体Agent只需要继承BaseAgent，实现自己的prompt构建逻辑即可
设计原则：单一职责，每个Agent只干一件事，输入输出格式固定
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# 把项目根目录加到Python搜索路径，解决模块导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.llm_client import llm_client


class BaseAgent:
    """
    Agent基类
    所有具体的Agent都继承自这个类，复用通用逻辑
    """

    # 子类需要重写的属性
    agent_name = "基础Agent"  # Agent名称，用于日志显示
    system_prompt = "你是一个专业的助手"  # 系统提示词，设定Agent角色
    output_format = "text"  # 输出格式："text" 或 "json"
    temperature = 0.7  # 温度参数，0-1之间，值越小越稳定

    def __init__(self):
        """
        初始化Agent
        """
        self.llm = llm_client  # 大模型客户端

    def build_prompt(self, **kwargs) -> str:
        """
        构建用户提示词
        子类必须重写这个方法，根据输入参数构建具体的prompt

        参数:
            **kwargs: 任意输入参数，由具体Agent决定

        返回:
            str: 构建好的用户提示词
        """
        # 基类不实现，由子类重写
        raise NotImplementedError("子类必须实现 build_prompt 方法")

    def validate_output(self, output: Any) -> bool:
        """
        校验输出结果是否符合要求
        子类可以重写这个方法，添加自定义校验逻辑

        参数:
            output: 大模型返回的结果（文本或字典）

        返回:
            bool: 校验是否通过
        """
        # 默认校验：只要不为空就通过
        if output is None:
            return False
        if isinstance(output, str) and not output.strip():
            return False
        if isinstance(output, dict) and len(output) == 0:
            return False
        return True

    def run(self, **kwargs) -> Any:
        """
        运行Agent的主方法
        这是Agent的统一入口，外部调用Agent都用这个方法

        参数:
            **kwargs: 任意输入参数，传给 build_prompt

        返回:
            大模型返回的结果（文本格式或字典格式，取决于output_format）
        """
        print(f"🤖 [{self.agent_name}] 开始运行...")

        # 第1步：构建提示词
        prompt = self.build_prompt(**kwargs)
        print(f"📝 [{self.agent_name}] 提示词构建完成，长度: {len(prompt)} 字符")

        # 第2步：调用大模型（带重试机制）
        max_attempts = 3  # 最多重试3次
        result = None

        for attempt in range(max_attempts):
            try:
                # 根据输出格式选择调用方式
                if self.output_format == "json":
                    # JSON格式输出
                    result = self.llm.call_json(
                        prompt=prompt,
                        system_prompt=self.system_prompt,
                        temperature=self.temperature
                    )
                else:
                    # 纯文本输出
                    result = self.llm.call(
                        prompt=prompt,
                        system_prompt=self.system_prompt,
                        temperature=self.temperature
                    )

                # 第3步：校验输出结果
                if self.validate_output(result):
                    print(f"✅ [{self.agent_name}] 运行成功")
                    return result
                else:
                    print(f"⚠️  [{self.agent_name}] 输出校验失败，第{attempt + 1}次重试...")

            except Exception as e:
                print(f"❌ [{self.agent_name}] 运行出错（第{attempt + 1}次）: {str(e)}")
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(1)  # 等1秒再重试

        # 重试都失败了
        raise Exception(f"[{self.agent_name}] 运行失败，已重试{max_attempts}次")

    def run_with_retry(self, **kwargs) -> Optional[Any]:
        """
        带异常捕获的运行方法（用于批量处理场景，单个失败不影响整体）
        失败时返回None，而不是抛出异常

        参数:
            **kwargs: 任意输入参数

        返回:
            成功返回结果，失败返回None
        """
        try:
            return self.run(**kwargs)
        except Exception as e:
            print(f"💥 [{self.agent_name}] 运行失败，跳过: {str(e)}")
            return None


# 测试代码（直接运行本文件时执行）
