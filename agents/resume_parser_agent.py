"""
简历解析Agent
功能：将简历文本解析为结构化数据，同时严格脱敏
输入：简历原始文本（已过脱敏工具）
输出：标准化的候选人信息（教育、工作、项目、技能、年限等）
合规要求：禁止提取性别、年龄、婚育、民族、籍贯、政治面貌、照片等敏感信息
"""

import os
import sys
import json
from typing import Dict, Any

# 把项目根目录加到Python搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent
from utils.desensitizer import desensitize_resume_data


class ResumeParserAgent(BaseAgent):
    """
    简历解析Agent
    从非结构化的简历文本中提取标准化信息
    """

    agent_name = "简历解析Agent"
    output_format = "json"
    temperature = 0.2  # 低温度，保证信息提取准确稳定

    system_prompt = """你是一位简历分析专家，负责提取简历中的关键信息。

【合规要求】
禁止提取或输出：性别、年龄、民族、籍贯、婚育、政治面貌、身份证号、照片。
简历中有这些信息直接忽略。

【原则】
只提取明确写出的信息，不猜测。严格输出JSON。"""

    def build_prompt(self, resume_text: str) -> str:
        """
        构建简历解析的提示词
        """
        prompt = f"""分析以下简历，提取关键信息，输出JSON。

【简历】
{resume_text}

输出格式：
{{
    "姓名": "",
    "所在城市": "",
    "工作年限": "",
    "到岗时间": "",
    "最高学历": "",
    "毕业院校": "",
    "专业": "",
    "技能清单": ["技能1", "技能2"],
    "工作经历摘要": "一句话总结工作经历",
    "核心项目": "最核心的1-2个项目名称和技术栈"
}}

要求：
1. 没有的信息填空字符串
2. 技能清单列8-15个核心技能
3. 不要输出性别、年龄、民族等敏感信息
"""
        return prompt

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        校验输出是否包含必要字段
        """
        required_fields = ["姓名", "工作年限", "最高学历", "技能清单"]
        if not isinstance(output, dict):
            return False
        for field in required_fields:
            if field not in output:
                print(f"⚠️  输出缺少必要字段: {field}")
                return False
        return True

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        运行Agent，返回前做脱敏检查
        """
        result = super().run(**kwargs)

        # 简单脱敏：移除敏感字段
        sensitive_keys = ["性别", "年龄", "民族", "籍贯", "婚姻状况", "政治面貌"]
        for key in sensitive_keys:
            result.pop(key, None)

        return result


# 测试代码
