"""
匹配度评估Agent
功能：对比结构化JD和结构化简历，给出匹配度评估
输入：结构化JD + 结构化简历
输出：匹配分、匹配点+证据、缺口、建议优先级
核心原则：有一分证据说一分话，所有结论必须可追溯
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


class MatcherAgent(BaseAgent):
    """
    匹配度评估Agent
    逐条对比JD要求和简历信息，给出可解释的匹配结果
    """

    agent_name = "匹配度评估Agent"
    output_format = "json"
    temperature = 0.2  # 低温度，保证评估客观稳定

    system_prompt = """你是一位严谨的招聘评估专家，负责对比岗位要求和候选人简历，给出客观的匹配度评估。

【核心评估原则】
1. 只认简历中明确写出的信息，绝对不能猜测、脑补或推断
2. 每个匹配点必须标注证据来源（简历中的哪段经历/哪个项目）
3. 每个缺口必须明确说明缺什么
4. 评分要客观，不要因为候选人某方面强就忽略其他方面的不足
5. 一票否决项不满足时，直接标记为"不推荐"，不管其他方面多优秀
6. 严格输出JSON格式，不要输出其他内容

【评分标准】
- 90-100分：完全匹配，所有硬性要求都满足，有多项加分项
- 75-89分：高度匹配，大部分硬性要求满足，少量缺口
- 60-74分：基本匹配，核心要求满足，但有明显缺口
- 40-59分：部分匹配，多项硬性要求不满足
- 40分以下：不匹配，核心要求不满足或有一票否决项"""

    def build_prompt(self, jd_data: Dict[str, Any], resume_data: Dict[str, Any]) -> str:
        """
        构建匹配度评估的提示词

        参数:
            jd_data: 结构化JD数据（JDParserAgent的输出）
            resume_data: 结构化简历数据（ResumeParserAgent的输出）
        """
        prompt = f"""请对比以下岗位要求和候选人简历，给出匹配度评估。

【岗位要求（JD）】
{json.dumps(jd_data, ensure_ascii=False, indent=2)}

【候选人简历】
{json.dumps(resume_data, ensure_ascii=False, indent=2)}

请按以下JSON格式输出评估结果：

{{
    "总体匹配分": 0-100的整数,
    "建议优先级": "优先查看" / "可查看" / "暂不推荐",
    "满足的硬性要求": [
        {{
            "要求": "JD中的具体要求",
            "简历证据": "简历中对应的具体经历或技能",
            "匹配程度": "完全匹配" / "基本匹配"
        }}
    ],
    "缺失的硬性要求": [
        {{
            "要求": "JD中的具体要求",
            "缺口说明": "简历中为什么不满足"
        }}
    ],
    "加分项匹配": [
        {{
            "加分项": "JD中的加分项",
            "简历证据": "简历中对应的经历",
            "加分说明": "为什么这是加分项"
        }}
    ],
    "一票否决项检查": {{
        "是否触发": true/false,
        "触发项": "如果触发，说明是哪一项；没有则为空字符串"
    }},
    "评估总结": "一段话总结该候选人的匹配情况，说明优势和不足"
}}

评估要求：
1. 逐条检查JD中的每一条硬性要求，不要遗漏
2. "简历证据"必须具体，引用简历中的原文或具体经历，不能写"简历中有提到"这种模糊的话
3. 如果候选人有JD没要求但很突出的能力，可以在评估总结中提到，但不影响评分
4. 建议优先级的判断标准：
   - 优先查看：匹配分75分以上，无一票否决项
   - 可查看：匹配分60-74分，无一票否决项
   - 暂不推荐：匹配分60分以下，或触发一票否决项
5. 评分要严格，不要给人情分
"""
        return prompt

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        校验输出是否包含必要字段
        """
        required_fields = ["总体匹配分", "建议优先级", "满足的硬性要求", "缺失的硬性要求", "评估总结"]
        if not isinstance(output, dict):
            return False
        for field in required_fields:
            if field not in output:
                print(f"⚠️  输出缺少必要字段: {field}")
                return False
        # 检查分数范围
        score = output.get("总体匹配分", 0)
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            print(f"⚠️  匹配分异常: {score}")
            return False
        return True


# 测试代码
