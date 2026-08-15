"""
JD解析Agent
功能：将自然语言的岗位描述（JD）解析为结构化数据
输入：JD原始文本
输出：结构化的岗位要求（硬性要求、加分项、岗位职责、权重等）
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


class JDParserAgent(BaseAgent):
    """
    JD解析Agent
    把模糊的招聘要求拆成可量化对比的维度
    """

    agent_name = "JD解析Agent"
    output_format = "json"
    temperature = 0.3  # 低温度，保证输出稳定

    system_prompt = """你是一位资深的HR招聘专家，擅长分析岗位描述（JD），提取结构化的招聘要求。
你的任务是把自然语言的JD拆解成清晰、可对比的结构化数据。

核心原则：
1. 只提取JD中明确写出的要求，不要自行脑补或添加
2. 硬性要求是"必须满足"的条件（如学历、年限、核心技能）
3. 加分项是"有了更好"的条件（如特定行业经验、额外技能）
4. 每条要求要具体、可判断，避免模糊表述
5. 严格输出JSON格式，不要输出其他内容"""

    def build_prompt(self, jd_text: str) -> str:
        """
        构建JD解析的提示词

        参数:
            jd_text: JD原始文本
        """
        prompt = f"""请分析以下岗位描述（JD），提取结构化的招聘要求。

【岗位描述原文】
{jd_text}

请按以下JSON格式输出：

{{
    "岗位名称": "岗位名称",
    "工作地点": "工作地点（如果有）",
    "薪资范围": "薪资范围（如果有）",
    "硬性要求": [
        "要求1（具体、可判断）",
        "要求2"
    ],
    "加分项": [
        "加分项1",
        "加分项2"
    ],
    "岗位职责": [
        "职责1",
        "职责2"
    ],
    "硬性要求权重": {{
        "学历": 权重分(0-10),
        "工作年限": 权重分(0-10),
        "核心技能": 权重分(0-10),
        "项目经验": 权重分(0-10)
    }},
    "一票否决项": [
        "如果有明确的一票否决条件，列在这里；没有则为空数组"
    ]
}}

注意事项：
1. 硬性要求权重：根据JD中该要求的重要程度打分，总分越高越重要
2. 一票否决项：如"必须本科及以上学历"、"必须有3年以上经验"等不满足就直接淘汰的条件
3. 如果JD中没有提到某项，对应字段填空字符串或空数组
4. 每条要求要具体到可以直接和简历对比，比如"熟悉Python"而不是"编程能力强"
"""
        return prompt

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        校验输出是否包含必要字段
        """
        required_fields = ["岗位名称", "硬性要求", "加分项", "岗位职责"]
        if not isinstance(output, dict):
            return False
        for field in required_fields:
            if field not in output:
                print(f"⚠️  输出缺少必要字段: {field}")
                return False
        return True


# 测试代码
