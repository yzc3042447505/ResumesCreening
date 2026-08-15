"""
流水线调度器模块
功能：串联所有Agent，完成完整的简历筛选流程
输入：JD文本 + 简历文本列表
输出：排序后的候选人结果列表
设计原则：单份简历失败不影响整体，异常捕获+跳过
"""

import os
import sys
from typing import List, Dict, Any

# 把项目根目录加到Python搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.jd_parser_agent import JDParserAgent
from agents.resume_parser_agent import ResumeParserAgent
from agents.matcher_agent import MatcherAgent
from agents.interview_agent import InterviewAgent
from utils.desensitizer import desensitize_text


class ScreeningPipeline:
    """
    简历筛选流水线
    串联所有Agent，完成从JD解析到面试题生成的完整流程
    """

    def __init__(self):
        """
        初始化流水线，创建所有Agent实例
        """
        self.jd_parser = JDParserAgent()
        self.resume_parser = ResumeParserAgent()
        self.matcher = MatcherAgent()
        self.interview_agent = InterviewAgent()

    def process_single_resume(self, jd_data: Dict[str, Any], resume_text: str,
                              file_name: str = "未知") -> Dict[str, Any]:
        """
        处理单份简历：解析→匹配→生成面试题

        参数:
            jd_data: 结构化JD数据
            resume_text: 简历原始文本
            file_name: 简历文件名（用于显示）

        返回:
            dict: 完整的候选人结果
        """
        print(f"\n📄 处理简历: {file_name}")

        # 第1步：简历文本脱敏预处理
        print("   🔒 文本脱敏...")
        desensitized_text = desensitize_text(resume_text)

        # 第2步：简历解析
        print("   📝 解析简历...")
        resume_data = self.resume_parser.run(resume_text=desensitized_text)
        if resume_data is None:
            raise Exception("简历解析失败")

        # 第3步：匹配度评估
        print("   🎯 匹配度评估...")
        match_result = self.matcher.run(jd_data=jd_data, resume_data=resume_data)
        if match_result is None:
            raise Exception("匹配度评估失败")

        # 第4步：生成面试问题
        print("   ❓ 生成面试题...")
        interview_result = self.interview_agent.run(
            jd_data=jd_data,
            resume_data=resume_data,
            match_result=match_result
        )
        if interview_result is None:
            raise Exception("面试题生成失败")

        # 组装结果
        result = {
            "file_name": file_name,
            "resume_data": resume_data,
            "match_result": match_result,
            "interview_questions": interview_result.get("面试问题", []),
            "interview_advice": interview_result.get("面试建议", ""),
        }

        score = match_result.get("总体匹配分", 0)
        priority = match_result.get("建议优先级", "待评估")
        print(f"   ✅ 完成，匹配分: {score}，优先级: {priority}")

        return result

    def run_full_pipeline(self, jd_text: str, resume_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        运行完整筛选流水线

        参数:
            jd_text: JD原始文本
            resume_list: 简历列表，每个元素是 {"file_name": 文件名, "text": 文本内容}

        返回:
            dict: {
                "jd_data": 结构化JD,
                "candidates": 候选人结果列表（按匹配分降序）,
                "total_count": 总简历数,
                "success_count": 成功处理数,
                "failed_count": 失败数,
                "failed_files": 失败的文件名列表
            }
        """
        print("=" * 60)
        print("🚀 开始运行简历筛选流水线")
        print("=" * 60)

        # 统计信息
        total_count = len(resume_list)
        success_count = 0
        failed_count = 0
        failed_files = []
        candidates = []

        # 第1步：解析JD
        print("\n📋 第1步：解析岗位描述（JD）")
        jd_data = self.jd_parser.run(jd_text=jd_text)
        if jd_data is None:
            raise Exception("JD解析失败，无法继续")
        print(f"✅ JD解析完成：{jd_data.get('岗位名称', '未知岗位')}")

        # 第2步：批量处理简历
        print(f"\n📄 第2步：批量处理简历（共 {total_count} 份）")

        for idx, resume_info in enumerate(resume_list, 1):
            file_name = resume_info.get("file_name", f"简历{idx}")
            resume_text = resume_info.get("text", "")

            print(f"\n--- [{idx}/{total_count}] {file_name} ---")

            try:
                # 处理单份简历
                result = self.process_single_resume(
                    jd_data=jd_data,
                    resume_text=resume_text,
                    file_name=file_name
                )
                candidates.append(result)
                success_count += 1

            except Exception as e:
                # 单份简历失败，记录并跳过
                print(f"   ❌ 处理失败: {str(e)}")
                failed_count += 1
                failed_files.append(file_name)
                continue

        # 第3步：按匹配分降序排序
        print("\n📊 第3步：按匹配分排序")
        candidates.sort(
            key=lambda x: x.get("match_result", {}).get("总体匹配分", 0),
            reverse=True
        )

        # 输出统计
        print("\n" + "=" * 60)
        print("📈 筛选完成统计")
        print("=" * 60)
        print(f"   总简历数: {total_count}")
        print(f"   成功处理: {success_count}")
        print(f"   处理失败: {failed_count}")
        if failed_files:
            print(f"   失败列表: {', '.join(failed_files)}")
        print(f"   最高匹配分: {candidates[0].get('match_result', {}).get('总体匹配分', 0) if candidates else 0}")
        print(f"   优先查看: {len([c for c in candidates if c.get('match_result', {}).get('建议优先级') == '优先查看'])} 人")
        print(f"   可查看: {len([c for c in candidates if c.get('match_result', {}).get('建议优先级') == '可查看'])} 人")
        print(f"   暂不推荐: {len([c for c in candidates if c.get('match_result', {}).get('建议优先级') == '暂不推荐'])} 人")
        print("=" * 60)

        return {
            "jd_data": jd_data,
            "candidates": candidates,
            "total_count": total_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_files": failed_files,
        }


# 测试代码
