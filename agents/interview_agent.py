"""
面试问题生成Agent
功能：基于JD、简历和匹配结果，生成定制化面试问题
输入：结构化JD + 结构化简历 + 匹配度结果
输出：3-5个面试问题，每个问题附带出题理由
出题逻辑：深挖匹配项 + 考察缺口项 + 验证核心能力
"""

import os
import sys
import json
from typing import Dict, Any, List

# 把项目根目录加到Python搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.base_agent import BaseAgent


class InterviewAgent(BaseAgent):
    """
    面试问题生成Agent
    为每个候选人生成针对性的面试问题
    """

    agent_name = "面试问题生成Agent"
    output_format = "json"
    temperature = 0.5  # 中等温度，既稳定又有一定创造性

    system_prompt = """你是一位经验丰富的技术面试官，擅长根据候选人的简历和岗位要求，设计有针对性的面试问题。

【出题原则】
1. 问题必须针对候选人的具体经历，不能是通用题库的套话
2. 每个问题都要有明确的考察目的，在"出题理由"中说明
3. 问题要有区分度，能真正考察出候选人的水平
4. 不要问和岗位无关的问题
5. 不要问性别、年龄、婚育等个人隐私问题
6. 严格输出JSON格式，不要输出其他内容

【问题类型】
- 深挖题：针对候选人简历中的项目经历和技能，追问细节和深度
- 缺口题：针对候选人不满足的要求，考察基础认知和学习能力
- 场景题：给一个实际工作场景，考察解决问题的能力"""

    def build_prompt(self, jd_data: Dict[str, Any], resume_data: Dict[str, Any],
                     match_result: Dict[str, Any]) -> str:
        """
        构建面试问题生成的提示词

        参数:
            jd_data: 结构化JD数据
            resume_data: 结构化简历数据
            match_result: 匹配度评估结果
        """
        prompt = f"""请根据以下信息，为该候选人设计3-5个面试问题。

【岗位要求】
{json.dumps(jd_data, ensure_ascii=False, indent=2)}

【候选人简历】
{json.dumps(resume_data, ensure_ascii=False, indent=2)}

【匹配度评估】
{json.dumps(match_result, ensure_ascii=False, indent=2)}

请按以下JSON格式输出：

{{
    "面试问题": [
        {{
            "问题": "具体的面试问题",
            "类型": "深挖题" / "缺口题" / "场景题",
            "考察点": "这个问题考察什么能力",
            "出题理由": "为什么问这个问题，和候选人/岗位的关系",
            "追问方向": "如果候选人回答了，可以追问什么"
        }}
    ],
    "面试建议": "一段话，给面试官的建议，比如重点考察什么、注意什么"
}}

出题要求：
1. 至少2道深挖题：针对候选人写的项目经历，追问技术细节、遇到的困难、解决方案
   - 比如："你在XX项目中用了FastAPI，请讲一下你是怎么设计接口权限控制的？"
   - 不要问"请介绍一下你的项目"这种泛泛的问题
2. 至少1道缺口题：针对候选人不满足的硬性要求，考察基础认知
   - 比如："你简历中没有LLM相关经验，你对大模型应用开发有了解吗？"
   - 不要问得像刁难，要考察学习潜力
3. 可以有1道场景题：结合岗位职责，给一个实际场景
   - 比如："如果让你设计一个支持百万用户的系统，你会怎么考虑？"
4. 问题要具体到候选人的真实经历，提到具体的项目名、技术名
5. 问题难度要适中，既有基础题也有深入题
"""
        return prompt

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        校验输出是否包含必要字段
        """
        if not isinstance(output, dict):
            return False
        if "面试问题" not in output:
            print("⚠️  输出缺少'面试问题'字段")
            return False
        questions = output["面试问题"]
        if not isinstance(questions, list) or len(questions) < 3:
            print("⚠️  面试问题数量不足3个")
            return False
        # 检查每个问题是否有必要字段
        for q in questions:
            if not all(k in q for k in ["问题", "类型", "考察点", "出题理由"]):
                print("⚠️  面试问题缺少必要字段")
                return False
        return True


# 测试代码
