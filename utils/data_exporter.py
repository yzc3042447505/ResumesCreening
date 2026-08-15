"""
数据导出工具模块
功能：将候选人筛选结果导出为Excel表格，方便HR横向对比和存档
说明：生成结构化的候选人对比表，包含关键信息和匹配度评分
"""

import pandas as pd
from typing import List, Dict, Any
from datetime import datetime


def safe_join_list(items: list, separator: str = "；") -> str:
    """
    安全地拼接列表，支持字符串和字典混合的列表

    参数:
        items: 列表，可以是字符串列表或字典列表
        separator: 分隔符

    返回:
        str: 拼接后的字符串
    """
    if not isinstance(items, list):
        return str(items) if items else ""

    str_list = []
    for item in items:
        if isinstance(item, dict):
            # 如果是字典，提取所有值拼接
            values = [str(v) for v in item.values() if v]
            str_list.append(" - ".join(values) if values else str(item))
        else:
            str_list.append(str(item))

    return separator.join(str_list)


def safe_join_questions(questions: list, separator: str = "\n") -> str:
    """
    安全地拼接面试问题列表

    参数:
        questions: 面试问题列表，可以是字符串或字典
        separator: 分隔符

    返回:
        str: 拼接后的字符串
    """
    if not isinstance(questions, list):
        return str(questions) if questions else ""

    str_list = []
    for i, q in enumerate(questions, 1):
        if isinstance(q, dict):
            q_text = q.get("问题", str(q))
            str_list.append(f"{i}. {q_text}")
        else:
            str_list.append(f"{i}. {q}")

    return separator.join(str_list)


def safe_join_skills(skills: list, separator: str = "、") -> str:
    """
    安全地拼接技能列表

    参数:
        skills: 技能列表
        separator: 分隔符

    返回:
        str: 拼接后的字符串
    """
    if not isinstance(skills, list):
        return str(skills) if skills else ""

    str_list = [str(s) for s in skills]
    return separator.join(str_list)


def export_candidates_to_excel(candidates: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    将候选人列表导出为Excel对比表

    参数:
        candidates: 候选人结果列表
        output_path: 输出文件路径

    返回:
        str: 生成的Excel文件路径
    """
    # 如果没有指定输出路径，自动生成带时间戳的文件名
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"候选人对比表_{timestamp}.xlsx"

    # 准备表格数据
    table_data = []

    for idx, candidate in enumerate(candidates, 1):
        # 提取简历数据
        resume = candidate.get("resume_data", {})
        basic_info = resume.get("基本信息", {})
        education = resume.get("教育背景", {})
        skills = resume.get("技能清单", [])

        # 提取匹配结果
        match = candidate.get("match_result", {})
        match_score = match.get("总体匹配分", 0)
        priority = match.get("建议优先级", "待评估")
        matched_points = match.get("满足的硬性要求", [])
        gaps = match.get("缺失的硬性要求", [])

        # 提取面试问题
        questions = candidate.get("interview_questions", [])

        # 组装一行数据
        row = {
            "序号": idx,
            "候选人": candidate.get("file_name", "未知"),
            "匹配分": match_score,
            "优先级": priority,
            "工作年限": basic_info.get("工作年限", ""),
            "所在城市": basic_info.get("所在城市", ""),
            "到岗时间": basic_info.get("到岗时间", ""),
            "最高学历": education.get("最高学历", ""),
            "毕业院校": education.get("毕业院校", ""),
            "核心技能": safe_join_skills(skills),
            "匹配亮点": safe_join_list(matched_points),
            "主要缺口": safe_join_list(gaps),
            "面试问题": safe_join_questions(questions),
        }

        table_data.append(row)

    # 创建DataFrame
    df = pd.DataFrame(table_data)

    # 按匹配分降序排序
    df = df.sort_values(by="匹配分", ascending=False)

    # 重新编号
    df["序号"] = range(1, len(df) + 1)

    # 导出到Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # 第一个sheet：候选人对比总表
        df.to_excel(writer, sheet_name="候选人对比表", index=False)

        # 调整列宽
        worksheet = writer.sheets["候选人对比表"]
        column_widths = {
            "A": 6,   # 序号
            "B": 15,  # 候选人
            "C": 8,   # 匹配分
            "D": 10,  # 优先级
            "E": 10,  # 工作年限
            "F": 10,  # 所在城市
            "G": 12,  # 到岗时间
            "H": 10,  # 最高学历
            "I": 15,  # 毕业院校
            "J": 30,  # 核心技能
            "K": 40,  # 匹配亮点
            "L": 30,  # 主要缺口
            "M": 50,  # 面试问题
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

        # 第二个sheet：匹配详情
        detail_data = []
        for idx, candidate in enumerate(candidates, 1):
            match = candidate.get("match_result", {})
            matched_points = match.get("满足的硬性要求", [])
            gaps = match.get("缺失的硬性要求", [])
            bonus = match.get("加分项匹配", [])

            for point in matched_points:
                detail_data.append({
                    "序号": idx,
                    "候选人": candidate.get("file_name", "未知"),
                    "类型": "匹配项",
                    "内容": safe_join_list([point], " - "),
                })

            for gap in gaps:
                detail_data.append({
                    "序号": idx,
                    "候选人": candidate.get("file_name", "未知"),
                    "类型": "缺口项",
                    "内容": safe_join_list([gap], " - "),
                })

            for b in bonus:
                detail_data.append({
                    "序号": idx,
                    "候选人": candidate.get("file_name", "未知"),
                    "类型": "加分项",
                    "内容": safe_join_list([b], " - "),
                })

        if detail_data:
            df_detail = pd.DataFrame(detail_data)
            df_detail.to_excel(writer, sheet_name="匹配详情", index=False)

            # 调整详情页列宽
            worksheet_detail = writer.sheets["匹配详情"]
            worksheet_detail.column_dimensions["A"].width = 6
            worksheet_detail.column_dimensions["B"].width = 15
            worksheet_detail.column_dimensions["C"].width = 10
            worksheet_detail.column_dimensions["D"].width = 60

    print(f"✅ Excel文件已生成: {output_path}")
    return output_path


def export_to_csv(candidates: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    导出为CSV格式

    参数:
        candidates: 候选人结果列表
        output_path: 输出文件路径

    返回:
        str: 生成的CSV文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"候选人对比表_{timestamp}.csv"

    # 准备表格数据
    table_data = []

    for idx, candidate in enumerate(candidates, 1):
        resume = candidate.get("resume_data", {})
        basic_info = resume.get("基本信息", {})
        education = resume.get("教育背景", {})
        skills = resume.get("技能清单", [])

        match = candidate.get("match_result", {})
        questions = candidate.get("interview_questions", [])

        row = {
            "序号": idx,
            "候选人": candidate.get("file_name", "未知"),
            "匹配分": match.get("总体匹配分", 0),
            "优先级": match.get("建议优先级", "待评估"),
            "工作年限": basic_info.get("工作年限", ""),
            "所在城市": basic_info.get("所在城市", ""),
            "最高学历": education.get("最高学历", ""),
            "核心技能": safe_join_skills(skills),
            "匹配亮点": safe_join_list(match.get("满足的硬性要求", [])),
            "主要缺口": safe_join_list(match.get("缺失的硬性要求", [])),
            "面试问题": safe_join_questions(questions, " | "),
        }
        table_data.append(row)

    df = pd.DataFrame(table_data)
    df = df.sort_values(by="匹配分", ascending=False)
    df["序号"] = range(1, len(df) + 1)

    # 导出CSV，用utf-8-sig编码保证Excel打开不乱码
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ CSV文件已生成: {output_path}")
    return output_path


# 测试代码
