"""
数据库工具模块
功能：使用SQLite保存筛选历史记录
说明：Python内置支持，单文件数据库，无需额外安装服务
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

# 把项目根目录加到Python搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# 数据库文件路径
DB_PATH = os.path.join(project_root, "data", "history.db")


def init_db():
    """
    初始化数据库，创建表和字段迁移
    """
    # 确保data目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建筛选任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jd_name TEXT NOT NULL,
            jd_content TEXT,
            resume_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建候选人结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            match_score INTEGER DEFAULT 0,
            priority TEXT DEFAULT '待评估',
            resume_data TEXT,
            match_result TEXT,
            interview_questions TEXT,
            interview_advice TEXT,
            status TEXT DEFAULT '待评估',
            note TEXT DEFAULT '',
            manual_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES screening_tasks (id) ON DELETE CASCADE
        )
    """)

    # 创建岗位模板表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            jd_content TEXT NOT NULL,
            description TEXT DEFAULT '',
            is_builtin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建面试纪要表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            tech_score INTEGER DEFAULT 0,
            project_score INTEGER DEFAULT 0,
            communication_score INTEGER DEFAULT 0,
            culture_score INTEGER DEFAULT 0,
            overall_score INTEGER DEFAULT 0,
            strengths TEXT DEFAULT '',
            concerns TEXT DEFAULT '',
            interviewer_comment TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            recommendation TEXT DEFAULT '',
            interviewer TEXT DEFAULT '',
            interview_date TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
        )
    """)

    # 字段迁移：给旧表加新字段（兼容已有的数据库）
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN status TEXT DEFAULT '待评估'")
    except sqlite3.OperationalError:
        pass  # 字段已存在，忽略

    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN note TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # 字段已存在，忽略

    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN manual_score INTEGER")
    except sqlite3.OperationalError:
        pass  # 字段已存在，忽略

    # 初始化内置模板（如果还没有的话）
    cursor.execute("SELECT COUNT(*) FROM job_templates WHERE is_builtin = 1")
    count = cursor.fetchone()[0]
    if count == 0:
        _init_builtin_templates(cursor)

    conn.commit()
    conn.close()


def _init_builtin_templates(cursor):
    """
    初始化内置岗位模板
    """
    builtin_templates = [
        {
            "name": "Python 后端开发工程师",
            "description": "互联网公司通用Python后端岗位JD",
            "jd_content": """岗位名称：Python后端开发工程师

岗位职责：
1. 负责公司核心业务系统的后端设计、开发与维护工作
2. 参与系统架构设计，持续优化系统性能和稳定性
3. 编写高质量、可维护的代码，编写单元测试，保证代码质量
4. 参与技术方案评审，解决开发过程中的技术难题
5. 与前端、产品、测试团队紧密协作，确保项目按时交付
6. 持续跟进新技术，推动技术升级和架构演进

任职要求：
1. 本科及以上学历，计算机相关专业，3年以上Python开发经验
2. 熟练掌握Python语言，熟悉常用Web框架（FastAPI/Django/Flask等）
3. 熟悉MySQL、PostgreSQL等关系型数据库，了解SQL优化
4. 熟悉Redis、MongoDB等NoSQL数据库的使用场景
5. 熟悉Linux系统，熟悉常用命令和Shell脚本编写
6. 了解微服务架构、消息队列（Kafka/RabbitMQ等）
7. 有良好的编码习惯，熟悉Git版本控制
8. 具备良好的问题分析和解决能力，有团队协作精神

加分项：
1. 有大流量、高并发系统开发经验
2. 有LLM/大模型应用开发经验
3. 有云原生、Docker、Kubernetes使用经验
4. 有开源项目贡献或技术博客输出
5. 熟悉Go、Java等其他编程语言

工作地点：北京/上海/深圳
薪资范围：20K-40K·14薪
"""
        },
        {
            "name": "前端开发工程师",
            "description": "互联网公司通用前端岗位JD",
            "jd_content": """岗位名称：前端开发工程师

岗位职责：
1. 负责公司Web产品的前端开发和维护工作
2. 与UI设计师、产品经理、后端工程师紧密协作，实现产品界面和交互
3. 优化前端性能，提升用户体验和页面加载速度
4. 封装通用组件和工具库，提高团队开发效率
5. 解决各种浏览器兼容性问题
6. 跟进前端技术发展，推动前端技术栈升级

任职要求：
1. 本科及以上学历，计算机相关专业，3年以上前端开发经验
2. 熟练掌握HTML、CSS、JavaScript，熟悉W3C标准
3. 熟练掌握React或Vue等主流前端框架
4. 熟悉前端工程化，了解Webpack、Vite等构建工具
5. 熟悉TypeScript，有类型安全开发经验
6. 了解Node.js，有后端开发经验者优先
7. 有良好的代码规范和文档习惯
8. 具备良好的沟通能力和团队协作精神

加分项：
1. 有移动端/H5开发经验，熟悉响应式布局
2. 有小程序、跨平台应用开发经验
3. 有可视化、低代码平台开发经验
4. 熟悉性能优化、安全防护等专项领域
5. 有开源项目贡献或技术博客输出

工作地点：北京/上海/深圳
薪资范围：18K-35K·14薪
"""
        },
        {
            "name": "产品经理",
            "description": "互联网公司通用产品经理JD",
            "jd_content": """岗位名称：产品经理

岗位职责：
1. 负责产品需求调研、分析和规划，制定产品路线图
2. 撰写产品需求文档（PRD），绘制产品原型和流程图
3. 协调研发、设计、测试、运营等团队，推动产品落地
4. 跟踪产品上线后的数据表现，持续优化产品体验
5. 收集用户反馈，挖掘用户需求，迭代产品功能
6. 进行竞品分析，了解行业动态和市场趋势
7. 参与产品运营策略制定，助力业务目标达成

任职要求：
1. 本科及以上学历，3年以上互联网产品经理经验
2. 熟练使用Axure、Figma、墨刀等原型设计工具
3. 具备良好的逻辑思维能力和用户体验意识
4. 具备较强的沟通协调能力和项目管理能力
5. 有数据驱动的产品思维，熟悉常用数据分析方法
6. 能够承受工作压力，适应快速迭代的工作节奏
7. 有To B或To C产品完整生命周期经验

加分项：
1. 有技术背景，懂研发流程和技术原理
2. 有0到1产品从无到有的经验
3. 有AI产品、SaaS产品经验
4. 有PMP等项目管理认证
5. 有用户增长、商业化相关经验

工作地点：北京/上海/深圳
薪资范围：20K-40K·14薪
"""
        },
        {
            "name": "测试开发工程师",
            "description": "互联网公司通用测试开发岗位JD",
            "jd_content": """岗位名称：测试开发工程师

岗位职责：
1. 负责公司产品的功能测试、接口测试、性能测试等质量保障工作
2. 设计和开发自动化测试框架和工具，提升测试效率
3. 参与需求评审，制定测试计划和测试用例
4. 跟踪和管理缺陷，推动问题及时解决
5. 搭建和维护CI/CD流水线，保障发布质量
6. 进行性能测试、安全测试等专项测试
7. 推动测试流程改进，提升整体研发效率和质量

任职要求：
1. 本科及以上学历，计算机相关专业，2年以上测试或测试开发经验
2. 熟悉软件测试理论和方法，熟悉测试流程
3. 掌握至少一种编程语言（Python/Java等）
4. 熟悉接口测试、自动化测试工具和框架
5. 熟悉MySQL等数据库，能编写SQL进行数据验证
6. 了解Linux系统和常用命令
7. 有良好的问题分析和定位能力
8. 具备良好的沟通能力和团队协作精神

加分项：
1. 有性能测试、安全测试经验
2. 有持续集成、DevOps相关经验
3. 有测试平台、测试工具开发经验
4. 有开发经验转测试开发
5. 熟悉云原生、容器化技术

工作地点：北京/上海/深圳
薪资范围：15K-30K·14薪
"""
        },
    ]

    for template in builtin_templates:
        cursor.execute("""
            INSERT INTO job_templates (name, jd_content, description, is_builtin, created_at, updated_at)
            VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))
        """, (template["name"], template["jd_content"], template["description"]))


def save_screening_result(jd_name: str, jd_content: str, candidates: List[Dict[str, Any]]) -> int:
    """
    保存一次筛选结果到数据库

    参数:
        jd_name: JD名称
        jd_content: JD原始内容
        candidates: 候选人结果列表

    返回:
        int: 任务ID
    """
    init_db()  # 确保表存在

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 插入筛选任务
        cursor.execute("""
            INSERT INTO screening_tasks (jd_name, jd_content, resume_count, success_count, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            jd_name,
            jd_content,
            len(candidates),
            len(candidates),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        task_id = cursor.lastrowid

        # 插入每个候选人
        for candidate in candidates:
            resume_data = json.dumps(candidate.get("resume_data", {}), ensure_ascii=False)
            match_result = json.dumps(candidate.get("match_result", {}), ensure_ascii=False)
            interview_questions = json.dumps(candidate.get("interview_questions", []), ensure_ascii=False)

            cursor.execute("""
                INSERT INTO candidates (
                    task_id, file_name, match_score, priority,
                    resume_data, match_result, interview_questions, interview_advice,
                    status, note, manual_score,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                candidate.get("file_name", "未知"),
                candidate.get("match_result", {}).get("总体匹配分", 0),
                candidate.get("match_result", {}).get("建议优先级", "待评估"),
                resume_data,
                match_result,
                interview_questions,
                candidate.get("interview_advice", ""),
                candidate.get("match_result", {}).get("建议优先级", "待评估"),  # 初始状态用AI优先级
                "",  # 备注初始为空
                None,  # 手动分初始为空，表示没改过
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        conn.commit()
        return task_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_task_list() -> List[Dict[str, Any]]:
    """
    获取所有筛选任务列表（按时间倒序）

    返回:
        list: 任务列表
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, jd_name, resume_count, success_count, created_at
        FROM screening_tasks
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    result = [dict(row) for row in rows]

    conn.close()
    return result


def get_task_detail(task_id: int) -> Optional[Dict[str, Any]]:
    """
    获取某次筛选任务的详细结果

    参数:
        task_id: 任务ID

    返回:
        dict: 任务详情，包含JD信息和候选人列表
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取任务信息
    cursor.execute("SELECT * FROM screening_tasks WHERE id = ?", (task_id,))
    task_row = cursor.fetchone()

    if not task_row:
        conn.close()
        return None

    task = dict(task_row)

    # 获取候选人列表
    cursor.execute("""
        SELECT * FROM candidates
        WHERE task_id = ?
        ORDER BY COALESCE(manual_score, match_score) DESC
    """, (task_id,))

    candidate_rows = cursor.fetchall()
    candidates = []

    for row in candidate_rows:
        candidate = dict(row)
        # 解析JSON字段
        candidate["resume_data"] = json.loads(candidate.get("resume_data", "{}"))
        candidate["match_result"] = json.loads(candidate.get("match_result", "{}"))
        candidate["interview_questions"] = json.loads(candidate.get("interview_questions", "[]"))
        candidates.append(candidate)

    task["candidates"] = candidates
    conn.close()
    return task


def delete_task(task_id: int) -> bool:
    """
    删除某次筛选任务（级联删除候选人）

    参数:
        task_id: 任务ID

    返回:
        bool: 是否删除成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 先删候选人
        cursor.execute("DELETE FROM candidates WHERE task_id = ?", (task_id,))
        # 再删任务
        cursor.execute("DELETE FROM screening_tasks WHERE id = ?", (task_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"删除失败: {e}")
        return False
    finally:
        conn.close()


def clear_all_history() -> bool:
    """
    清空所有历史记录

    返回:
        bool: 是否清空成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM candidates")
        cursor.execute("DELETE FROM screening_tasks")
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"清空失败: {e}")
        return False
    finally:
        conn.close()


# ============================================
# 岗位模板相关方法
# ============================================

def get_template_list() -> List[Dict[str, Any]]:
    """
    获取所有岗位模板列表

    返回:
        list: 模板列表，按创建时间倒序
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, description, jd_content, is_builtin, created_at, updated_at
        FROM job_templates
        ORDER BY is_builtin DESC, updated_at DESC
    """)

    rows = cursor.fetchall()
    result = [dict(row) for row in rows]

    conn.close()
    return result


def get_template(template_id: int) -> Optional[Dict[str, Any]]:
    """
    获取单个模板详情

    参数:
        template_id: 模板ID

    返回:
        dict: 模板详情
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM job_templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    template = dict(row)
    conn.close()
    return template


def add_template(name: str, jd_content: str, description: str = "") -> int:
    """
    新增岗位模板

    参数:
        name: 模板名称
        jd_content: JD内容
        description: 模板描述

    返回:
        int: 新模板ID
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO job_templates (name, jd_content, description, is_builtin, created_at, updated_at)
            VALUES (?, ?, ?, 0, datetime('now'), datetime('now'))
        """, (name, jd_content, description))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        print(f"添加模板失败: {e}")
        return 0
    finally:
        conn.close()


def update_template(template_id: int, name: str, jd_content: str, description: str = "") -> bool:
    """
    更新岗位模板

    参数:
        template_id: 模板ID
        name: 模板名称
        jd_content: JD内容
        description: 模板描述

    返回:
        bool: 是否更新成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE job_templates
            SET name = ?, jd_content = ?, description = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (name, jd_content, description, template_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"更新模板失败: {e}")
        return False
    finally:
        conn.close()


def delete_template(template_id: int) -> bool:
    """
    删除岗位模板（内置模板不能删）

    参数:
        template_id: 模板ID

    返回:
        bool: 是否删除成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查是不是内置模板
        cursor.execute("SELECT is_builtin FROM job_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        if row and row[0] == 1:
            print("内置模板不能删除")
            return False

        cursor.execute("DELETE FROM job_templates WHERE id = ?", (template_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"删除模板失败: {e}")
        return False
    finally:
        conn.close()


# ============================================
# 面试纪要相关方法
# ============================================

def get_interview_note(candidate_id: int) -> Optional[Dict[str, Any]]:
    """
    获取候选人的面试纪要

    参数:
        candidate_id: 候选人ID

    返回:
        dict: 面试纪要，没有则返回None
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM interview_notes
        WHERE candidate_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (candidate_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    note = dict(row)
    conn.close()
    return note


def save_interview_note(
    candidate_id: int,
    tech_score: int,
    project_score: int,
    communication_score: int,
    culture_score: int,
    overall_score: int,
    strengths: str = "",
    concerns: str = "",
    interviewer_comment: str = "",
    summary: str = "",
    recommendation: str = "",
    interviewer: str = "",
    interview_date: str = ""
) -> int:
    """
    保存面试纪要（有则更新，无则新增）

    参数:
        candidate_id: 候选人ID
        tech_score: 技术能力评分（1-5）
        project_score: 项目经验评分（1-5）
        communication_score: 沟通表达评分（1-5）
        culture_score: 文化匹配评分（1-5）
        overall_score: 综合评价评分（1-5）
        strengths: 优势总结
        concerns: 风险/顾虑
        interviewer_comment: 面试官评语
        summary: AI生成的总结
        recommendation: 录用建议
        interviewer: 面试官姓名
        interview_date: 面试日期

    返回:
        int: 纪要ID
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查是否已有纪要
        cursor.execute("SELECT id FROM interview_notes WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()

        if row:
            # 更新已有纪要
            note_id = row[0]
            cursor.execute("""
                UPDATE interview_notes SET
                    tech_score = ?,
                    project_score = ?,
                    communication_score = ?,
                    culture_score = ?,
                    overall_score = ?,
                    strengths = ?,
                    concerns = ?,
                    interviewer_comment = ?,
                    summary = ?,
                    recommendation = ?,
                    interviewer = ?,
                    interview_date = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (
                tech_score, project_score, communication_score, culture_score, overall_score,
                strengths, concerns, interviewer_comment, summary, recommendation,
                interviewer, interview_date, note_id
            ))
        else:
            # 新增纪要
            cursor.execute("""
                INSERT INTO interview_notes (
                    candidate_id, tech_score, project_score, communication_score,
                    culture_score, overall_score, strengths, concerns,
                    interviewer_comment, summary, recommendation,
                    interviewer, interview_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                candidate_id, tech_score, project_score, communication_score,
                culture_score, overall_score, strengths, concerns,
                interviewer_comment, summary, recommendation,
                interviewer, interview_date
            ))
            note_id = cursor.lastrowid

        conn.commit()
        return note_id
    except Exception as e:
        conn.rollback()
        print(f"保存面试纪要失败: {e}")
        return 0
    finally:
        conn.close()


def delete_interview_note(note_id: int) -> bool:
    """
    删除面试纪要

    参数:
        note_id: 纪要ID

    返回:
        bool: 是否删除成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM interview_notes WHERE id = ?", (note_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"删除面试纪要失败: {e}")
        return False
    finally:
        conn.close()


def update_candidate_status(candidate_id: int, status: str) -> bool:
    """
    更新候选人状态

    参数:
        candidate_id: 候选人ID
        status: 新状态（待评估/优先查看/约面/待定/淘汰）

    返回:
        bool: 是否更新成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE candidates
            SET status = ?
            WHERE id = ?
        """, (status, candidate_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"更新状态失败: {e}")
        return False
    finally:
        conn.close()


def update_candidate_note(candidate_id: int, note: str) -> bool:
    """
    更新候选人备注

    参数:
        candidate_id: 候选人ID
        note: 备注内容

    返回:
        bool: 是否更新成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE candidates
            SET note = ?
            WHERE id = ?
        """, (note, candidate_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"更新备注失败: {e}")
        return False
    finally:
        conn.close()


def update_candidate_score(candidate_id: int, manual_score: int) -> bool:
    """
    更新候选人手动评分

    参数:
        candidate_id: 候选人ID
        manual_score: 手动评分（0-100）

    返回:
        bool: 是否更新成功
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE candidates
            SET manual_score = ?
            WHERE id = ?
        """, (manual_score, candidate_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"更新分数失败: {e}")
        return False
    finally:
        conn.close()


def get_candidate(candidate_id: int) -> Optional[Dict[str, Any]]:
    """
    获取单个候选人详情

    参数:
        candidate_id: 候选人ID

    返回:
        dict: 候选人详情
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    candidate = dict(row)
    # 解析JSON字段
    candidate["resume_data"] = json.loads(candidate.get("resume_data", "{}"))
    candidate["match_result"] = json.loads(candidate.get("match_result", "{}"))
    candidate["interview_questions"] = json.loads(candidate.get("interview_questions", "[]"))

    conn.close()
    return candidate


# 测试代码
