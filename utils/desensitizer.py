"""
脱敏工具模块
功能：过滤简历中的敏感个人信息，确保合规性
说明：在简历文本进入大模型之前、解析结果输出之后，各过一遍脱敏，双重保障
合规依据：《个人信息保护法》，避免基于性别、年龄、婚育等敏感信息做招聘决策
"""

import re
from typing import Dict, Any


def desensitize_text(text: str) -> str:
    """
    对纯文本进行脱敏处理，移除/替换敏感信息

    参数:
        text: 原始文本

    返回:
        str: 脱敏后的文本
    """
    result = text

    # ============================================
    # 1. 身份信息类
    # ============================================

    # 身份证号（18位或15位）
    result = re.sub(r'\d{17}[\dXx]', '[身份证号已隐藏]', result)
    result = re.sub(r'\d{15}', '[身份证号已隐藏]', result)

    # 手机号（11位，以1开头）
    result = re.sub(r'1[3-9]\d{9}', '[手机号已隐藏]', result)

    # 邮箱地址
    result = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[邮箱已隐藏]', result)

    # ============================================
    # 2. 个人属性类（招聘决策不应依据的信息）
    # ============================================

    # 性别信息
    gender_patterns = [
        r'性别[：:]\s*[男女]',
        r'性\s*别[：:]\s*[男女]',
        r'^[男女]\s*$',
    ]
    for pattern in gender_patterns:
        result = re.sub(pattern, '性别：[已隐藏]', result, flags=re.MULTILINE)

    # 年龄/出生日期
    age_patterns = [
        r'年龄[：:]\s*\d+\s*岁?',
        r'年\s*龄[：:]\s*\d+\s*岁?',
        r'出生[日期年月]*[：:]\s*\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?',
        r'出\s*生[日期年月]*[：:]\s*\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?',
        r'出生日期[：:]\s*\d{4}年',
        r'生日[：:]\s*\d{1,2}月\d{1,2}日',
    ]
    for pattern in age_patterns:
        result = re.sub(pattern, '年龄：[已隐藏]', result)

    # 民族
    nation_patterns = [
        r'民族[：:]\s*[\u4e00-\u9fa5]+族',
        r'民\s*族[：:]\s*[\u4e00-\u9fa5]+族',
    ]
    for pattern in nation_patterns:
        result = re.sub(pattern, '民族：[已隐藏]', result)

    # 籍贯/户籍
    native_patterns = [
        r'籍贯[：:]\s*[\u4e00-\u9fa5]+',
        r'籍\s*贯[：:]\s*[\u4e00-\u9fa5]+',
        r'户籍[：:]\s*[\u4e00-\u9fa5]+',
        r'户\s*籍[：:]\s*[\u4e00-\u9fa5]+',
        r'户口所在地[：:]\s*[\u4e00-\u9fa5]+',
    ]
    for pattern in native_patterns:
        result = re.sub(pattern, '籍贯：[已隐藏]', result)

    # 婚育状况
    marriage_patterns = [
        r'婚育[：:]\s*[\u4e00-\u9fa5]+',
        r'婚姻状况[：:]\s*[\u4e00-\u9fa5]+',
        r'婚\s*姻\s*状\s*况[：:]\s*[\u4e00-\u9fa5]+',
        r'婚姻状态[：:]\s*[\u4e00-\u9fa5]+',
        r'未婚|已婚|离异|丧偶',
        r'已育|未育|有小孩|有孩子',
    ]
    for pattern in marriage_patterns:
        result = re.sub(pattern, '[婚育信息已隐藏]', result)

    # 政治面貌
    political_patterns = [
        r'政治面貌[：:]\s*[\u4e00-\u9fa5]+',
        r'政\s*治\s*面\s*貌[：:]\s*[\u4e00-\u9fa5]+',
        r'中共党员|共产党员|共青团员|群众|民主党派',
    ]
    for pattern in political_patterns:
        result = re.sub(pattern, '[政治面貌已隐藏]', result)

    # ============================================
    # 3. 照片信息（文本中提到的照片）
    # ============================================

    photo_patterns = [
        r'照片[：:]\s*[\u4e00-\u9fa5]*',
        r'照\s*片[：:]\s*[\u4e00-\u9fa5]*',
        r'（照片）|\(照片\)',
        r'[【\[]照片[】\]]',
    ]
    for pattern in photo_patterns:
        result = re.sub(pattern, '[照片信息已隐藏]', result)

    return result


def desensitize_resume_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    对结构化的简历数据进行脱敏（第二重保障）
    在简历解析完成后，对结构化数据再做一次脱敏检查

    参数:
        data: 结构化的简历数据字典

    返回:
        dict: 脱敏后的简历数据
    """
    # 需要移除的敏感字段列表
    sensitive_fields = [
        '性别', '年龄', '出生日期', '生日',
        '民族', '籍贯', '户籍', '户口所在地',
        '婚姻状况', '婚姻状态', '婚育状况', '婚育',
        '政治面貌', '照片', '身份证号',
        'gender', 'age', 'birthday', 'nation',
        'marital_status', 'political_status',
    ]

    result = {}

    for key, value in data.items():
        # 如果是敏感字段，直接跳过
        if key in sensitive_fields or any(s in key for s in sensitive_fields):
            continue

        # 如果值是字典，递归处理
        if isinstance(value, dict):
            result[key] = desensitize_resume_data(value)
        # 如果值是列表，遍历处理
        elif isinstance(value, list):
            result[key] = [
                desensitize_resume_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        # 其他类型直接保留
        else:
            result[key] = value

    return result


def check_sensitive_info(text: str) -> list:
    """
    检查文本中是否还包含敏感信息（用于自检）

    参数:
        text: 要检查的文本

    返回:
        list: 发现的敏感信息类型列表
    """
    found = []

    # 检查各类敏感信息
    checks = {
        '身份证号': r'\d{17}[\dXx]',
        '手机号': r'1[3-9]\d{9}',
        '邮箱': r'[\w.-]+@[\w.-]+\.\w+',
        '性别': r'性别[：:]\s*[男女]',
        '年龄': r'年龄[：:]\s*\d+',
        '民族': r'民族[：:]\s*[\u4e00-\u9fa5]+族',
        '籍贯': r'籍贯[：:]\s*[\u4e00-\u9fa5]+',
        '婚育': r'未婚|已婚|已育|未育',
        '政治面貌': r'中共党员|共青团员|群众',
    }

    for info_type, pattern in checks.items():
        if re.search(pattern, text):
            found.append(info_type)

    return found


# 测试代码（直接运行本文件时执行）
