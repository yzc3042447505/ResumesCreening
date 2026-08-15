"""
候选人初筛助手 - Enterprise级SaaS界面
设计风格：极简科技感、Bento Grid、玻璃拟态、细线条图标
参考：Linear, Vercel, Raycast
"""

import os
import sys
import json
import streamlit as st
import pandas as pd

# 确保工作目录是当前文件所在目录（解决部署时子目录路径问题）
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
os.chdir(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.pipeline import ScreeningPipeline
from utils.file_loader import extract_text_from_file, get_file_name
from utils.data_exporter import export_candidates_to_excel
from utils.llm_client import llm_client
from utils.database import (
    save_screening_result,
    get_task_list,
    get_task_detail,
    delete_task,
    clear_all_history
)


# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="候选人初筛助手",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================
# 注入自定义CSS - Enterprise级SaaS风格
# ============================================
def inject_custom_css():
    custom_css = """
    <style>
    /* ========== 全局基础 ========== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
        letter-spacing: -0.01em;
    }

    /* 主背景 - 冷钛白/浅灰基底 */
    .stApp {
        background: #fafafa;
        color: #09090b;
    }

    /* 主内容区 */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ========== 侧边栏 ========== */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e4e4e7;
        padding-top: 1rem;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }

    /* 侧边栏标题 */
    [data-testid="stSidebar"] h3 {
        font-size: 0.875rem !important;
        font-weight: 600;
        color: #09090b;
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
    }

    [data-testid="stSidebar"] h4 {
        font-size: 0.8rem !important;
        font-weight: 500;
        color: #71717a;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ========== 上传组件 ========== */
    [data-testid="stFileUploader"] {
        background: #fafafa;
        border: 1px dashed #d4d4d8;
        border-radius: 10px;
        padding: 1rem;
        transition: all 0.2s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #6366f1;
        background: #f5f5ff;
    }

    [data-testid="stFileUploader"] section {
        padding: 0;
    }

    [data-testid="stFileUploader"] section small {
        color: #a1a1aa !important;
        font-size: 0.75rem;
    }

    /* ========== 按钮样式 ========== */
    /* 主按钮 - Indigo渐变微光 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(99, 102, 241, 0.2);
        width: 100%;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    }

    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
    }

    /* 次要按钮 */
    .stButton > button {
        background: #ffffff;
        color: #09090b !important;
        border: 1px solid #e4e4e7;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: #f4f4f5;
        border-color: #d4d4d8;
        color: #09090b !important;
    }

    /* ========== 标题样式 ========== */
    h1 {
        font-size: 1.75rem !important;
        font-weight: 700;
        color: #09090b !important;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem !important;
        line-height: 1.2;
    }

    h2 {
        font-size: 1.25rem !important;
        font-weight: 600;
        color: #09090b !important;
        letter-spacing: -0.02em;
        margin-bottom: 1rem;
    }

    h3 {
        font-size: 1rem !important;
        font-weight: 600;
        color: #09090b !important;
        letter-spacing: -0.01em;
    }

    /* 副标题/说明文字 */
    .stCaption {
        color: #52525b !important;
        font-size: 0.875rem !important;
        font-weight: 400;
    }

    /* ========== 标签页 - 分段控件风格 ========== */
    .stTabs {
        margin-bottom: 1.5rem;
    }

    .stTabs [data-testid="stTabList"] {
        gap: 0.25rem;
        background: #f4f4f5;
        padding: 0.25rem;
        border-radius: 10px;
        border: 1px solid #e4e4e7;
        width: fit-content;
    }

    .stTabs [data-testid="stTab"] {
        background: transparent;
        color: #71717a !important;
        border-radius: 7px;
        padding: 0.5rem 1.25rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        border: none;
    }

    .stTabs [data-testid="stTab"] p {
        color: #71717a !important;
        font-size: 0.875rem;
        font-weight: 500;
    }

    .stTabs [data-testid="stTab"][aria-selected="true"] {
        background: #ffffff;
        color: #09090b !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    .stTabs [data-testid="stTab"][aria-selected="true"] p {
        color: #09090b !important;
        font-weight: 600;
    }

    .stTabs [data-testid="stTab"]:hover {
        color: #09090b !important;
    }

    .stTabs [data-testid="stTab"]:hover p {
        color: #09090b !important;
    }

    /* ========== 指标卡片 ========== */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        transition: all 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: #d4d4d8;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #71717a !important;
        font-size: 0.75rem !important;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stMetricValue"] {
        color: #09090b !important;
        font-size: 1.5rem !important;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-top: 0.25rem;
    }

    /* ========== 展开器 - 卡片风格 ========== */
    .streamlit-expanderHeader {
        background: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 10px !important;
        padding: 0.875rem 1.125rem;
        font-weight: 500;
        color: #09090b !important;
        transition: all 0.2s ease;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }

    .streamlit-expanderHeader:hover {
        background: #fafafa;
        border-color: #d4d4d8;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    .streamlit-expanderContent {
        background: #ffffff;
        border-radius: 0 0 10px 10px;
        padding: 1rem 1.125rem;
        border: 1px solid #e4e4e7;
        border-top: none;
        margin-top: -0.5rem;
        margin-bottom: 0.5rem;
        color: #09090b;
    }

    /* ========== 信息框 ========== */
    .stInfo {
        background: #f5f5ff;
        border: 1px solid #e0e7ff;
        border-left: 3px solid #6366f1;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #4338ca !important;
        font-size: 0.875rem;
    }

    .stInfo p {
        color: #4338ca !important;
        font-size: 0.875rem;
    }

    .stSuccess {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 3px solid #22c55e;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #166534 !important;
        font-size: 0.875rem;
    }

    .stSuccess p {
        color: #166534 !important;
        font-size: 0.875rem;
    }

    .stWarning {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 3px solid #f59e0b;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #92400e !important;
        font-size: 0.875rem;
    }

    .stWarning p {
        color: #92400e !important;
        font-size: 0.875rem;
    }

    .stError {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 3px solid #ef4444;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #991b1b !important;
        font-size: 0.875rem;
    }

    .stError p {
        color: #991b1b !important;
        font-size: 0.875rem;
    }

    /* ========== 进度条 ========== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        border-radius: 4px;
    }

    .stProgress > div > div > div {
        background: #e4e4e7;
        border-radius: 4px;
        height: 6px;
    }

    /* ========== 分隔线 ========== */
    hr {
        border: none;
        height: 1px;
        background: #e4e4e7;
        margin: 1.5rem 0;
    }

    /* ========== 代码块 ========== */
    code {
        background: #f4f4f5;
        color: #6366f1;
        padding: 0.125rem 0.375rem;
        border-radius: 4px;
        font-size: 0.85em;
        font-family: 'SF Mono', 'Fira Code', monospace;
    }

    /* ========== 滚动条 ========== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: #d4d4d8;
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #a1a1aa;
    }

    /* ========== Bento Card 样式 ========== */
    .bento-card {
        background: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 14px;
        padding: 1.5rem;
        transition: all 0.25s ease;
        height: 100%;
    }

    .bento-card:hover {
        border-color: #c7d2fe;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.08);
        transform: translateY(-2px);
    }

    .bento-card-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        font-size: 1.25rem;
        color: white;
    }

    .bento-card-title {
        font-size: 1rem;
        font-weight: 600;
        color: #09090b;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }

    .bento-card-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .bento-card-list li {
        color: #52525b;
        font-size: 0.875rem;
        padding: 0.375rem 0;
        padding-left: 1.25rem;
        position: relative;
    }

    .bento-card-list li::before {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #6366f1;
    }

    /* ========== AI 徽章 ========== */
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.25rem 0.75rem;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #6366f1;
    }

    /* ========== 步骤条 ========== */
    .stepper {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin: 2rem 0;
    }

    .step-item {
        flex: 1;
        text-align: center;
        position: relative;
    }

    .step-number {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #ffffff;
        border: 2px solid #e4e4e7;
        color: #71717a;
        font-weight: 600;
        font-size: 0.875rem;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.75rem;
        transition: all 0.2s ease;
    }

    .step-item.active .step-number {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-color: #6366f1;
        color: white;
    }

    .step-title {
        font-size: 0.875rem;
        font-weight: 500;
        color: #09090b;
        margin-bottom: 0.25rem;
    }

    .step-desc {
        font-size: 0.75rem;
        color: #71717a;
    }

    .step-line {
        position: absolute;
        top: 16px;
        left: 50%;
        width: 100%;
        height: 2px;
        background: #e4e4e7;
        z-index: 0;
    }

    .step-item:last-child .step-line {
        display: none;
    }

    /* ========== 技能标签 ========== */
    .skill-tag {
        display: inline-block;
        padding: 0.25rem 0.625rem;
        background: #f4f4f5;
        border: 1px solid #e4e4e7;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        color: #52525b;
        margin: 0.125rem;
        transition: all 0.15s ease;
    }

    .skill-tag:hover {
        background: #eef2ff;
        border-color: #c7d2fe;
        color: #4f46e5;
    }

    /* ========== 优先级标签 ========== */
    .priority-tag {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .priority-high {
        background: #dcfce7;
        color: #166534;
    }

    .priority-medium {
        background: #fef3c7;
        color: #92400e;
    }

    .priority-low {
        background: #f4f4f5;
        color: #52525b;
    }

    /* ========== 面试问题卡片 ========== */
    .question-card {
        background: #fafafa;
        border: 1px solid #e4e4e7;
        border-left: 3px solid #6366f1;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .question-text {
        font-weight: 600;
        color: #09090b;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .question-meta {
        font-size: 0.75rem;
        color: #71717a;
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .question-meta span {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }

    /* ========== 匹配分显示 ========== */
    .score-display {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        padding: 1rem;
    }

    .score-number {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .score-label {
        font-size: 0.75rem;
        color: #71717a;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* ========== 表格 ========== */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e4e4e7;
    }

    /* ========== 加载动画 ========== */
    .stSpinner > div {
        border-color: #e4e4e7 !important;
        border-top-color: #6366f1 !important;
    }

    /* ========== 侧边栏底部提示 ========== */
    .sidebar-tip {
        background: #fafafa;
        border: 1px solid #e4e4e7;
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 1rem;
    }

    .sidebar-tip-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #09090b;
        margin-bottom: 0.375rem;
        display: flex;
        align-items: center;
        gap: 0.375rem;
    }

    .sidebar-tip-text {
        font-size: 0.75rem;
        color: #71717a;
        line-height: 1.5;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


# 注入CSS
inject_custom_css()


# ============================================
# 初始化
# ============================================
@st.cache_resource
def get_pipeline():
    return ScreeningPipeline()


def init_app():
    """
    应用初始化接口
    程序启动时自动调用，做一些初始化工作：
    - 创建必要的目录
    - 清理旧的临时文件
    - 初始化数据库
    """
    # 创建临时目录
    temp_dirs = ["temp_uploads", "temp_exports"]
    for d in temp_dirs:
        dir_path = os.path.join(current_dir, d)
        os.makedirs(dir_path, exist_ok=True)

    # 清理旧的导出文件（只保留最近1天）
    exports_dir = os.path.join(current_dir, "temp_exports")
    if os.path.exists(exports_dir):
        import time
        now = time.time()
        cutoff = now - 24 * 3600  # 24小时前
        cleaned = 0
        for filename in os.listdir(exports_dir):
            filepath = os.path.join(exports_dir, filename)
            if os.path.isfile(filepath):
                mtime = os.path.getmtime(filepath)
                if mtime < cutoff:
                    try:
                        os.remove(filepath)
                        cleaned += 1
                    except:
                        pass
        if cleaned > 0:
            print(f"🧹 已清理 {cleaned} 个旧的导出文件")

    # 初始化数据库
    from utils.database import init_db
    init_db()

    print("✅ 应用初始化完成")


def main():
    """主函数"""
    # 应用初始化
    init_app()

    # 顶部Header
    col1, col2 = st.columns([8, 1])
    with col1:
        st.markdown("### ⚡ 候选人初筛助手")
        st.caption("AI 智能辅助 · 匹配有据可溯 · 决策由人完成")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="ai-badge">'
            '<span>✨</span>'
            'AI Powered'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # 标签页切换
    tab1, tab2, tab3 = st.tabs(["  🚀 开始筛选  ", "  📚 历史记录  ", "  📋 岗位模板  "])

    with tab1:
        show_screening_tab()

    with tab2:
        show_history_tab()

    with tab3:
        show_templates_tab()


# ============================================
# 筛选标签页
# ============================================
def show_screening_tab():
    """显示筛选标签页"""
    # 侧边栏：上传区
    with st.sidebar:
        # ========== API配置区域 ==========
        st.markdown("### ⚙️ API配置")
        st.markdown("---")

        if not llm_client.is_configured():
            st.warning("请先配置大模型API密钥")

            # 预设服务商
            providers = {
                "火山方舟（豆包）": {
                    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                    "model": "doubao-seed-2.1-pro",
                    "help": "在火山方舟控制台创建API Key，模型填写接入点ID（ep-开头）或模型名称"
                },
                "DeepSeek": {
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "help": "在platform.deepseek.com申请API Key"
                },
                "OpenAI": {
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4o-mini",
                    "help": "在platform.openai.com申请API Key"
                },
                "自定义（兼容OpenAI格式）": {
                    "base_url": "https://api.example.com/v1",
                    "model": "your-model-name",
                    "help": "任何兼容OpenAI Chat Completions格式的API服务"
                }
            }

            provider_names = list(providers.keys())
            selected_provider = st.selectbox(
                "选择API服务商",
                options=provider_names,
                key="api_provider",
                help="选择你的大模型API服务商"
            )

            default_config = providers[selected_provider]

            api_key = st.text_input(
                "API Key",
                type="password",
                key="api_key_input",
                help=default_config["help"]
            )

            base_url = st.text_input(
                "API Base URL",
                value=default_config["base_url"],
                key="api_base_url",
                help="兼容OpenAI格式的API地址"
            )

            model = st.text_input(
                "模型名称",
                value=default_config["model"],
                key="api_model",
                help="填写要使用的模型名称或接入点ID"
            )

            if st.button("✅ 保存配置", type="primary", use_container_width=True):
                if api_key:
                    llm_client.configure(api_key=api_key, base_url=base_url, model=model)
                    st.session_state["api_configured"] = True
                    st.success("配置成功！可以开始使用了")
                    st.rerun()
                else:
                    st.error("请输入API Key")

            st.markdown("---")
        else:
            st.success("✅ API已配置")
            st.caption(f"模型: {llm_client.model}")
            if st.button("重新配置", use_container_width=True):
                # 重置配置
                llm_client.api_key = ""
                llm_client.headers["Authorization"] = "Bearer "
                st.session_state["api_configured"] = False
                st.rerun()
            st.markdown("---")

        # ========== API配置区域结束 ==========

        st.markdown("### 📤 上传文件")
        st.markdown("---")

        # JD上传卡片
        st.markdown("#### 📋 岗位描述 (JD)")
        jd_file = st.file_uploader(
            "拖拽或点击上传",
            type=["pdf", "docx", "txt"],
            key="jd_uploader",
            help="支持 PDF / DOCX / TXT 格式"
        )

        # 或选用模板
        st.markdown("<div style='text-align:center; color:#a1a1aa; margin:0.5rem 0;'>— 或选用模板 —</div>", unsafe_allow_html=True)

        from utils.database import get_template_list
        templates = get_template_list()
        template_options = ["— 选择岗位模板 —"] + [f"{t['name']}{' [内置]' if t['is_builtin'] else ''}" for t in templates]
        selected_template_idx = st.selectbox(
            "选择岗位模板",
            options=range(len(template_options)),
            format_func=lambda x: template_options[x],
            key="template_selector",
            index=0,
            help="选择内置或自定义的岗位模板，无需上传JD"
        )

        selected_template = None
        if selected_template_idx > 0:
            selected_template = templates[selected_template_idx - 1]

        st.markdown("---")

        # 简历上传卡片
        st.markdown("#### 👥 候选人简历")
        resume_files = st.file_uploader(
            "拖拽或点击上传（可多选）",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="resume_uploader",
            help="支持 PDF / DOCX 格式，可批量上传"
        )

        st.markdown("---")

        # 判断是否可以开始（有JD文件 或 选了模板）
        can_start = llm_client.is_configured() and resume_files and (jd_file or selected_template)

        # 开始按钮
        start_button = st.button(
            "⚡ 开始智能筛选",
            type="primary",
            use_container_width=True,
            disabled=not can_start
        )

        if not can_start and resume_files:
            st.caption("💡 请上传JD文件或选择岗位模板")

        # 底部提示
        st.markdown("""
        <div class="sidebar-tip">
            <div class="sidebar-tip-title">
                <span>💡</span> 使用提示
            </div>
            <div class="sidebar-tip-text">
                支持批量上传简历，建议一次不超过 20 份，以获得最佳体验。
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 主区域
    if start_button and resume_files and (jd_file or selected_template):
        run_screening(jd_file, resume_files, selected_template)
    else:
        show_welcome()


# ============================================
# 欢迎页面 - Bento Grid风格
# ============================================
def show_welcome():
    """显示欢迎页面"""

    # Bento Cards - 三大功能
    st.markdown("#### 🚀 核心功能")
    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="bento-card">
            <div class="bento-card-icon">📄</div>
            <div class="bento-card-title">智能解析</div>
            <ul class="bento-card-list">
                <li>自动提取 JD 结构化要求</li>
                <li>简历信息智能提取与脱敏</li>
                <li>支持 PDF / DOCX 格式</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="bento-card">
            <div class="bento-card-icon">🎯</div>
            <div class="bento-card-title">精准匹配</div>
            <ul class="bento-card-list">
                <li>逐条对比岗位要求</li>
                <li>每个匹配点带证据溯源</li>
                <li>自动排序优先级</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="bento-card">
            <div class="bento-card-icon">✨</div>
            <div class="bento-card-title">定制面试题</div>
            <ul class="bento-card-list">
                <li>针对项目经历深挖</li>
                <li>针对短板能力考察</li>
                <li>每题带出题理由</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("---")

    # 使用步骤 - 水平步骤条
    st.markdown("#### 📝 使用步骤")
    st.markdown("")

    steps = [
        ("1", "上传 JD", "上传岗位描述文件"),
        ("2", "上传简历", "批量上传候选人简历"),
        ("3", "智能筛选", "AI 自动分析匹配"),
        ("4", "查看结果", "查看匹配度和面试题"),
        ("5", "导出对比", "导出候选人对比表"),
        ("6", "历史记录", "随时查看历史筛选"),
    ]

    cols = st.columns(6)
    for i, (num, title, desc) in enumerate(steps):
        with cols[i]:
            active = "active" if i < 3 else ""
            st.markdown(f"""
            <div class="step-item {active}">
                <div class="step-number">{num}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("---")
    st.caption("⚠️ 本工具仅提供 AI 辅助筛选建议，最终录用决策请由招聘者人工做出")


# ============================================
# 运行筛选流程
# ============================================
def run_screening(jd_file, resume_files, selected_template=None):
    """运行筛选流程"""

    temp_dir = os.path.join(current_dir, "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 获取JD内容和名称（从文件 或 从模板）
        jd_name = ""
        jd_text = ""

        if selected_template:
            # 从模板获取JD
            from utils.database import get_template
            template = get_template(selected_template["id"])
            if template:
                jd_name = template["name"]
                jd_text = template["jd_content"]
                st.info(f"📋 使用岗位模板: {jd_name}")
        elif jd_file:
            # 从文件读取JD
            jd_path = os.path.join(temp_dir, jd_file.name)
            with open(jd_path, "wb") as f:
                f.write(jd_file.getbuffer())

            _, jd_text = extract_text_from_file(jd_path)
            jd_name = get_file_name(jd_file.name)

        if not jd_text:
            st.error("❌ 无法获取JD内容，请重新上传或选择模板")
            return

        # 读取简历
        resume_list = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.markdown(
            '<div style="color: #6366f1; font-weight: 500; font-size: 0.875rem;">📄 正在读取简历文件...</div>',
            unsafe_allow_html=True
        )

        for idx, resume_file in enumerate(resume_files):
            resume_path = os.path.join(temp_dir, resume_file.name)
            with open(resume_path, "wb") as f:
                f.write(resume_file.getbuffer())

            try:
                _, resume_text = extract_text_from_file(resume_path)
                file_name = get_file_name(resume_file.name)
                resume_list.append({
                    "file_name": file_name,
                    "text": resume_text
                })
            except Exception as e:
                st.warning(f"⚠️ 文件 {resume_file.name} 读取失败: {str(e)}")

            progress_bar.progress((idx + 1) / len(resume_files))

        status_text.markdown(
            f'<div style="color: #22c55e; font-weight: 500; font-size: 0.875rem;">✅ 成功读取 {len(resume_list)} 份简历</div>',
            unsafe_allow_html=True
        )

        # 运行流水线
        st.markdown("---")
        st.markdown("#### 🔄 AI 筛选进行中")

        pipeline = get_pipeline()

        with st.spinner("AI 正在分析简历，请稍候..."):
            result = pipeline.run_full_pipeline(
                jd_text=jd_text,
                resume_list=resume_list
            )

        # 保存历史记录
        task_id = None
        try:
            task_id = save_screening_result(jd_name, jd_text, result["candidates"])
            st.success(f"💾 结果已保存到历史记录（任务 ID: {task_id}）")

            # 重新从数据库读取，带上候选人ID，支持编辑
            from utils.database import get_task_detail
            detail = get_task_detail(task_id)
            if detail:
                result["candidates"] = detail["candidates"]
                result["task_id"] = task_id
        except Exception as e:
            st.warning(f"⚠️ 保存历史记录失败: {str(e)}")

        # 显示结果
        show_results(result)

    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# ============================================
# 展示筛选结果
# ============================================
def show_results(result):
    """展示筛选结果"""

    st.success("🎉 筛选完成！")

    # 统计指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总简历数", result["total_count"])
    with col2:
        st.metric("成功处理", result["success_count"])
    with col3:
        priority_count = len([c for c in result["candidates"]
                              if c.get("status") == "优先查看" or c.get("match_result", {}).get("建议优先级") == "优先查看"])
        st.metric("优先查看", priority_count)
    with col4:
        if result["candidates"]:
            # 取最高分（手动分优先）
            scores = []
            for c in result["candidates"]:
                s = c.get("manual_score") or c.get("match_result", {}).get("总体匹配分", 0)
                scores.append(s)
            max_score = max(scores) if scores else 0
        else:
            max_score = 0
        st.metric("最高匹配分", f"{max_score}分")

    if result.get("failed_count", 0) > 0:
        st.warning(f"⚠️ {result['failed_count']} 份简历处理失败: {', '.join(result.get('failed_files', []))}")

    st.markdown("---")

    # 筛选和导出
    col_filter, col_export, col_rest = st.columns([2, 1, 5])

    with col_filter:
        # 状态筛选
        filter_status = st.selectbox(
            "按状态筛选",
            options=["全部", "待评估", "优先查看", "约面", "待定", "淘汰"],
            key="filter_status_result"
        )

    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 导出 Excel", type="secondary", use_container_width=True):
            export_path = export_candidates_to_excel(result["candidates"])
            with open(export_path, "rb") as f:
                st.download_button(
                    "⬇️ 下载对比表",
                    f.read(),
                    file_name=os.path.basename(export_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    # 应用筛选
    filtered_candidates = result["candidates"]
    if filter_status != "全部":
        filtered_candidates = [
            c for c in filtered_candidates
            if c.get("status", "") == filter_status
        ]

    # 批量操作栏
    with st.expander("⚡ 批量操作", expanded=False):
        col_batch1, col_batch2, col_batch3, col_batch4 = st.columns([3, 2, 2, 2])

        with col_batch1:
            # 多选候选人
            candidate_options = [f"{c['file_name']} ({c.get('status', '待评估')})" for c in filtered_candidates]
            candidate_ids = [c['id'] for c in filtered_candidates]

            selected_indices = st.multiselect(
                "选择候选人",
                options=range(len(candidate_options)),
                format_func=lambda x: candidate_options[x],
                key="batch_select_result"
            )

            selected_ids = [candidate_ids[i] for i in selected_indices]

        with col_batch2:
            batch_status = st.selectbox(
                "批量设置状态",
                options=["待评估", "优先查看", "约面", "待定", "淘汰"],
                key="batch_status_result"
            )

        with col_batch3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 批量改状态", use_container_width=True):
                if selected_ids:
                    from utils.database import update_candidate_status
                    for cid in selected_ids:
                        update_candidate_status(cid, batch_status)
                    st.success(f"✅ 已将 {len(selected_ids)} 人状态改为「{batch_status}」")
                    st.rerun()
                else:
                    st.warning("请先选择候选人")

        with col_batch4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📊 批量导出", use_container_width=True):
                if selected_ids:
                    selected_candidates = [c for c in filtered_candidates if c['id'] in selected_ids]
                    export_path = export_candidates_to_excel(selected_candidates)
                    with open(export_path, "rb") as f:
                        st.download_button(
                            "⬇️ 下载选中的",
                            f.read(),
                            file_name=os.path.basename(export_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="batch_download_result"
                        )
                else:
                    st.warning("请先选择候选人")

    st.markdown(f"#### 👥 候选人列表（{len(filtered_candidates)} 人）")
    render_candidate_cards(filtered_candidates, editable=True, show_checkboxes=True, checkbox_prefix="result")


# ============================================
# 渲染候选人卡片
# ============================================
def render_candidate_cards(candidates, editable=True, show_checkboxes=False, checkbox_prefix=""):
    """
    渲染候选人卡片列表

    参数:
        candidates: 候选人列表
        editable: 是否可编辑（显示状态/分数/备注修改）
        show_checkboxes: 是否显示复选框（用于批量操作）
        checkbox_prefix: 复选框的key前缀，避免重复
    """
    # 状态选项
    status_options = ["待评估", "优先查看", "约面", "待定", "淘汰"]

    # 批量操作栏
    if show_checkboxes and candidates:
        st.markdown("")

        with st.container():
            col_select, col_status, col_apply, col_export, col_count = st.columns([1.5, 2, 1.5, 1.5, 2])

            with col_select:
                # 全选/反选
                select_all = st.checkbox("全选", key=f"{checkbox_prefix}_select_all")
                if select_all:
                    for c in candidates:
                        st.session_state[f"{checkbox_prefix}_selected_{c['id']}"] = True

            with col_status:
                # 批量改状态
                batch_status = st.selectbox(
                    "批量改状态",
                    options=status_options,
                    key=f"{checkbox_prefix}_batch_status"
                )

            with col_apply:
                st.markdown("<br>", unsafe_allow_html=True)
                apply_btn = st.button("✅ 应用", key=f"{checkbox_prefix}_apply_status", use_container_width=True)
                if apply_btn:
                    selected_ids = [
                        c["id"] for c in candidates
                        if st.session_state.get(f"{checkbox_prefix}_selected_{c['id']}", False)
                    ]
                    if selected_ids:
                        from utils.database import update_candidate_status
                        for cid in selected_ids:
                            update_candidate_status(cid, batch_status)
                        st.success(f"✅ 已将 {len(selected_ids)} 人状态改为「{batch_status}」")
                        st.rerun()
                    else:
                        st.warning("⚠️ 请先选择候选人")

            with col_export:
                st.markdown("<br>", unsafe_allow_html=True)
                export_btn = st.button("📤 批量导出", key=f"{checkbox_prefix}_batch_export", use_container_width=True)
                if export_btn:
                    selected_candidates = [
                        c for c in candidates
                        if st.session_state.get(f"{checkbox_prefix}_selected_{c['id']}", False)
                    ]
                    if selected_candidates:
                        export_path = export_candidates_to_excel(selected_candidates)
                        with open(export_path, "rb") as f:
                            st.download_button(
                                "⬇️ 下载",
                                f.read(),
                                file_name=os.path.basename(export_path),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"{checkbox_prefix}_batch_download",
                                use_container_width=True
                            )
                    else:
                        st.warning("⚠️ 请先选择候选人")

            with col_count:
                selected_count = sum(
                    1 for c in candidates
                    if st.session_state.get(f"{checkbox_prefix}_selected_{c['id']}", False)
                )
                st.markdown(f"<div style='text-align:right; padding-top:1.5rem; color:#52525b; font-weight:500;'>已选 {selected_count} / {len(candidates)} 人</div>", unsafe_allow_html=True)

        st.markdown("---")

    for idx, candidate in enumerate(candidates, 1):
        match = candidate["match_result"]
        resume = candidate["resume_data"]

        # 显示分数：有手动分显示手动分，否则显示AI分
        manual_score = candidate.get("manual_score")
        ai_score = match.get("总体匹配分", 0)
        score = manual_score if manual_score is not None else ai_score
        score_label = "手动分" if manual_score is not None else "AI 分"

        # 显示状态：用数据库里的status，没有就用AI的priority
        status = candidate.get("status") or match.get("建议优先级", "待评估")
        note = candidate.get("note", "") or ""

        # 状态样式
        if status in ["优先查看", "约面"]:
            priority_class = "priority-high"
            priority_text = status
        elif status in ["可查看", "待定"]:
            priority_class = "priority-medium"
            priority_text = status
        elif status == "淘汰":
            priority_class = "priority-low"
            priority_text = status
        else:
            priority_class = "priority-low"
            priority_text = status

        # 卡片标题（带复选框）
        title = f"  {idx}. {candidate['file_name']}    ·    {score} 分 ({score_label})    ·    {priority_text}"

        if show_checkboxes and candidate.get("id"):
            col_check, col_title = st.columns([1, 20])
            with col_check:
                st.checkbox(
                    "",
                    key=f"{checkbox_prefix}_selected_{candidate['id']}",
                    label_visibility="collapsed"
                )
            with col_title:
                expander = st.expander(title, expanded=(idx <= 2))
        else:
            expander = st.expander(title, expanded=(idx <= 2))

        with expander:
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("**📊 匹配概览**")

                # 匹配分大数字
                st.markdown(f"""
                <div class="score-display">
                    <div class="score-number">{score}</div>
                    <div class="score-label">{score_label} / 100</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"- **工作年限**: {resume.get('工作年限', '未知')}")
                st.markdown(f"- **所在城市**: {resume.get('所在城市', '未知')}")
                st.markdown(f"- **最高学历**: {resume.get('最高学历', '未知')}")
                st.markdown(f"- **毕业院校**: {resume.get('毕业院校', '未知')}")
                st.markdown(f"- **到岗时间**: {resume.get('到岗时间', '未知')}")

                # 技能标签
                skills = resume.get("技能清单", [])
                if skills:
                    st.markdown("**💡 核心技能**")
                    skill_html = "".join([
                        f'<span class="skill-tag">{s}</span>'
                        for s in skills[:12]
                    ])
                    st.markdown(skill_html, unsafe_allow_html=True)

            with col_right:
                st.markdown("**✅ 满足的要求**")
                matched = match.get("满足的硬性要求", [])
                if matched:
                    for item in matched:
                        if isinstance(item, dict):
                            req = item.get("要求", "")
                            evidence = item.get("简历证据", "")
                            st.markdown(f"- ✅ **{req}**")
                            if evidence:
                                st.caption(f"  💬 证据: {evidence}")
                        else:
                            st.markdown(f"- ✅ {item}")
                else:
                    st.markdown("- 暂无")

                st.markdown("**❌ 缺失的要求**")
                gaps = match.get("缺失的硬性要求", [])
                if gaps:
                    for item in gaps:
                        if isinstance(item, dict):
                            req = item.get("要求", "")
                            reason = item.get("缺口说明", "")
                            st.markdown(f"- ❌ **{req}**")
                            if reason:
                                st.caption(f"  💬 说明: {reason}")
                        else:
                            st.markdown(f"- ❌ {item}")
                else:
                    st.markdown("- 🎉 无明显缺口")

                # 加分项
                bonus = match.get("加分项匹配", [])
                if bonus:
                    st.markdown("**⭐ 加分项**")
                    for item in bonus:
                        if isinstance(item, dict):
                            st.markdown(f"- ⭐ {item.get('加分项', '')}")
                        else:
                            st.markdown(f"- ⭐ {item}")

            st.markdown("---")

            # 评估总结
            summary = match.get("评估总结", "")
            if summary:
                st.info(f"💡 **评估总结**: {summary}")

            # 面试问题
            st.markdown("**❓ 定制面试问题**")
            questions = candidate.get("interview_questions", [])
            for q_idx, q in enumerate(questions, 1):
                if isinstance(q, dict):
                    q_text = q.get("问题", "")
                    q_type = q.get("类型", "")
                    q_point = q.get("考察点", "")
                    q_reason = q.get("出题理由", "")
                    q_followup = q.get("追问方向", "")

                    type_label = "深挖题" if q_type == "深挖题" else "缺口题" if q_type == "缺口题" else "场景题"

                    st.markdown(f"""
                    <div class="question-card">
                        <div class="question-text">{q_idx}. {q_text}</div>
                        <div class="question-meta">
                            <span>🏷️ {type_label}</span>
                            <span>🎯 {q_point}</span>
                        </div>
                        {f'<div class="question-meta" style="margin-top: 0.375rem;"><span>💡 出题理由: {q_reason}</span></div>' if q_reason else ''}
                        {f'<div class="question-meta" style="margin-top: 0.25rem;"><span>🔗 可追问: {q_followup}</span></div>' if q_followup else ''}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"{q_idx}. {q}")

            # 面试建议
            advice = candidate.get("interview_advice", "")
            if advice:
                st.success(f"💡 **面试建议**: {advice}")

            # 人工修正区域
            if editable and candidate.get("id"):
                st.markdown("---")
                st.markdown("**✏️ 人工修正**")

                with st.form(key=f"edit_form_{candidate['id']}"):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        new_status = st.selectbox(
                            "候选人状态",
                            options=status_options,
                            index=status_options.index(status) if status in status_options else 0,
                            key=f"status_{candidate['id']}"
                        )

                        new_score = st.number_input(
                            "匹配分（手动调整）",
                            min_value=0,
                            max_value=100,
                            value=int(score),
                            key=f"score_{candidate['id']}"
                        )

                    with col2:
                        new_note = st.text_area(
                            "备注",
                            value=note,
                            placeholder="添加备注，比如：前同事内推、薪资要求高、需要复试等",
                            height=80,
                            key=f"note_{candidate['id']}"
                        )

                    submit_col1, submit_col2, submit_col3 = st.columns([1, 1, 4])
                    with submit_col1:
                        submitted = st.form_submit_button("💾 保存修改", type="primary", use_container_width=True)

                    if submitted:
                        from utils.database import update_candidate_status, update_candidate_score, update_candidate_note
                        update_candidate_status(candidate["id"], new_status)
                        update_candidate_score(candidate["id"], new_score)
                        update_candidate_note(candidate["id"], new_note)
                        st.success("✅ 修改已保存")
                        st.rerun()

                # 显示已有备注
                if note:
                    st.info(f"📝 当前备注: {note}")

            # 面试纪要区域
            if editable and candidate.get("id"):
                st.markdown("---")
                st.markdown("**📋 面试纪要**")

                from utils.database import get_interview_note, save_interview_note
                existing_note = get_interview_note(candidate["id"])

                # 评分维度
                score_dimensions = [
                    ("tech_score", "技术能力", "专业技能、知识深度"),
                    ("project_score", "项目经验", "过往项目匹配度、深度"),
                    ("communication_score", "沟通表达", "逻辑清晰、表达流畅"),
                    ("culture_score", "文化匹配", "价值观、团队协作、稳定性"),
                    ("overall_score", "综合评价", "整体印象、录用建议"),
                ]

                with st.form(key=f"interview_form_{candidate['id']}"):
                    # 5个维度评分
                    col1, col2, col3, col4, col5 = st.columns(5)
                    cols = [col1, col2, col3, col4, col5]

                    scores = {}
                    for i, (key, name, desc) in enumerate(score_dimensions):
                        with cols[i]:
                            default_score = existing_note.get(key, 3) if existing_note else 3
                            scores[key] = st.slider(
                                name,
                                min_value=1,
                                max_value=5,
                                value=default_score,
                                help=desc,
                                key=f"score_{key}_{candidate['id']}"
                            )

                    st.markdown("")

                    # 优势和顾虑
                    col_left, col_right = st.columns([1, 1])
                    with col_left:
                        strengths = st.text_area(
                            "✅ 优势总结",
                            value=existing_note.get("strengths", "") if existing_note else "",
                            placeholder="候选人的主要优势、亮点...",
                            height=80,
                            key=f"strengths_{candidate['id']}"
                        )
                    with col_right:
                        concerns = st.text_area(
                            "⚠️ 风险/顾虑",
                            value=existing_note.get("concerns", "") if existing_note else "",
                            placeholder="需要注意的地方、潜在风险...",
                            height=80,
                            key=f"concerns_{candidate['id']}"
                        )

                    # 面试官评语
                    interviewer_comment = st.text_area(
                        "💬 面试官评语",
                        value=existing_note.get("interviewer_comment", "") if existing_note else "",
                        placeholder="面试官的整体评价、补充说明...",
                        height=80,
                        key=f"comment_{candidate['id']}"
                    )

                    # 面试官和日期
                    col_info1, col_info2, col_btn1, col_btn2 = st.columns([2, 2, 1.5, 1.5])

                    with col_info1:
                        interviewer = st.text_input(
                            "面试官",
                            value=existing_note.get("interviewer", "") if existing_note else "",
                            placeholder="面试官姓名",
                            key=f"interviewer_{candidate['id']}"
                        )

                    with col_info2:
                        interview_date = st.text_input(
                            "面试日期",
                            value=existing_note.get("interview_date", "") if existing_note else "",
                            placeholder="YYYY-MM-DD",
                            key=f"date_{candidate['id']}"
                        )

                    with col_btn1:
                        generate_btn = st.form_submit_button("✨ AI 生成纪要", type="primary", use_container_width=True)

                    with col_btn2:
                        save_btn = st.form_submit_button("💾 保存", use_container_width=True)

                    if generate_btn:
                        with st.spinner("AI 正在生成面试纪要..."):
                            # 构建prompt
                            avg_score = sum(scores.values()) / len(scores)
                            if avg_score >= 4.5:
                                rec = "强烈推荐"
                            elif avg_score >= 3.5:
                                rec = "推荐"
                            elif avg_score >= 2.5:
                                rec = "待定"
                            else:
                                rec = "不推荐"

                            # 简单的AI生成逻辑（基于模板，后续可以接大模型）
                            summary_parts = []
                            summary_parts.append(f"候选人整体表现{'优秀' if avg_score >= 4 else '良好' if avg_score >= 3 else '一般'}，综合评分 {avg_score:.1f}/5 分。")

                            if scores["tech_score"] >= 4:
                                summary_parts.append(f"技术能力{'突出' if scores['tech_score'] >= 5 else '较强'}。")
                            elif scores["tech_score"] <= 2:
                                summary_parts.append("技术能力有待提升。")

                            if scores["project_score"] >= 4:
                                summary_parts.append(f"项目经验{'丰富' if scores['project_score'] >= 5 else '较丰富'}，与岗位匹配度高。")
                            elif scores["project_score"] <= 2:
                                summary_parts.append("项目经验相对不足。")

                            if scores["communication_score"] >= 4:
                                summary_parts.append("沟通表达清晰流畅，逻辑思维好。")
                            elif scores["communication_score"] <= 2:
                                summary_parts.append("沟通表达能力有待加强。")

                            if strengths:
                                summary_parts.append(f"主要优势：{strengths}。")
                            if concerns:
                                summary_parts.append(f"需要关注：{concerns}。")

                            if interviewer_comment:
                                summary_parts.append(f"面试官评价：{interviewer_comment}。")

                            summary_parts.append(f"录用建议：**{rec}**。")

                            summary = " ".join(summary_parts)

                            # 保存到数据库
                            save_interview_note(
                                candidate_id=candidate["id"],
                                tech_score=scores["tech_score"],
                                project_score=scores["project_score"],
                                communication_score=scores["communication_score"],
                                culture_score=scores["culture_score"],
                                overall_score=scores["overall_score"],
                                strengths=strengths,
                                concerns=concerns,
                                interviewer_comment=interviewer_comment,
                                summary=summary,
                                recommendation=rec,
                                interviewer=interviewer,
                                interview_date=interview_date
                            )

                            st.success("✅ 面试纪要已生成并保存！")
                            st.rerun()

                    if save_btn:
                        # 计算录用建议
                        avg_score = sum(scores.values()) / len(scores)
                        if avg_score >= 4.5:
                            rec = "强烈推荐"
                        elif avg_score >= 3.5:
                            rec = "推荐"
                        elif avg_score >= 2.5:
                            rec = "待定"
                        else:
                            rec = "不推荐"

                        save_interview_note(
                            candidate_id=candidate["id"],
                            tech_score=scores["tech_score"],
                            project_score=scores["project_score"],
                            communication_score=scores["communication_score"],
                            culture_score=scores["culture_score"],
                            overall_score=scores["overall_score"],
                            strengths=strengths,
                            concerns=concerns,
                            interviewer_comment=interviewer_comment,
                            summary=existing_note.get("summary", "") if existing_note else "",
                            recommendation=rec,
                            interviewer=interviewer,
                            interview_date=interview_date
                        )
                        st.success("✅ 已保存！")
                        st.rerun()

                # 显示已生成的纪要
                if existing_note and existing_note.get("summary"):
                    st.markdown("")
                    st.markdown("**📄 已生成的面试纪要**")

                    # 评分概览
                    avg_score = (
                        existing_note["tech_score"] +
                        existing_note["project_score"] +
                        existing_note["communication_score"] +
                        existing_note["culture_score"] +
                        existing_note["overall_score"]
                    ) / 5

                    rec = existing_note.get("recommendation", "")
                    rec_color = "#10b981" if rec == "强烈推荐" else "#6366f1" if rec == "推荐" else "#f59e0b" if rec == "待定" else "#ef4444"

                    st.markdown(f"""
                    <div style="background:#fafafa; border:1px solid #e4e4e7; border-radius:10px; padding:1rem; margin-bottom:1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                            <div style="font-size:1.25rem; font-weight:700; color:#18181b;">综合评分：{avg_score:.1f} / 5</div>
                            <div style="background:{rec_color}; color:white; padding:0.25rem 0.75rem; border-radius:20px; font-size:0.875rem; font-weight:600;">{rec}</div>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(5,1fr); gap:0.5rem; text-align:center;">
                            <div>
                                <div style="font-size:1.1rem; font-weight:600; color:#6366f1;">{existing_note['tech_score']}</div>
                                <div style="font-size:0.75rem; color:#71717a;">技术能力</div>
                            </div>
                            <div>
                                <div style="font-size:1.1rem; font-weight:600; color:#6366f1;">{existing_note['project_score']}</div>
                                <div style="font-size:0.75rem; color:#71717a;">项目经验</div>
                            </div>
                            <div>
                                <div style="font-size:1.1rem; font-weight:600; color:#6366f1;">{existing_note['communication_score']}</div>
                                <div style="font-size:0.75rem; color:#71717a;">沟通表达</div>
                            </div>
                            <div>
                                <div style="font-size:1.1rem; font-weight:600; color:#6366f1;">{existing_note['culture_score']}</div>
                                <div style="font-size:0.75rem; color:#71717a;">文化匹配</div>
                            </div>
                            <div>
                                <div style="font-size:1.1rem; font-weight:600; color:#6366f1;">{existing_note['overall_score']}</div>
                                <div style="font-size:0.75rem; color:#71717a;">综合评价</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 纪要内容
                    st.markdown(existing_note["summary"])

                    # 面试官信息
                    if existing_note.get("interviewer") or existing_note.get("interview_date"):
                        st.caption(f"👤 面试官：{existing_note.get('interviewer', '未填写')} | 📅 面试日期：{existing_note.get('interview_date', '未填写')}")

    st.markdown("---")
    st.caption("⚠️ 以上结果为 AI 辅助筛选建议，最终录用决策请由招聘者人工做出")


# ============================================
# 历史记录标签页
# ============================================
def show_history_tab():
    """显示历史记录标签页"""
    st.markdown("#### 📚 历史筛选记录")

    # 初始化 session_state
    if 'viewing_task_id' not in st.session_state:
        st.session_state.viewing_task_id = None

    tasks = get_task_list()

    if not tasks:
        st.info("暂无历史记录，去「开始筛选」标签页创建第一条吧！")
        return

    # 统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总筛选次数", len(tasks))
    with col2:
        total_resumes = sum(t["resume_count"] for t in tasks)
        st.metric("累计处理简历", total_resumes)
    with col3:
        latest = tasks[0]["created_at"] if tasks else "-"
        st.metric("最近筛选时间", latest)

    st.markdown("---")

    # 清空按钮
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ 清空全部历史", type="secondary"):
            if clear_all_history():
                st.success("✅ 已清空全部历史记录")
                st.session_state.viewing_task_id = None
                st.rerun()
            else:
                st.error("❌ 清空失败")

    st.markdown("#### 📋 筛选任务列表")

    for task in tasks:
        with st.expander(
            f"  📝 {task['jd_name']}    ·    {task['resume_count']} 份简历    ·    {task['created_at']}",
            expanded=(st.session_state.viewing_task_id == task["id"])
        ):
            # 任务信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("任务 ID", task["id"])
            with col2:
                st.metric("简历数量", task["resume_count"])
            with col3:
                st.metric("成功处理", task["success_count"])
            with col4:
                st.metric("筛选时间", task["created_at"])

            # 操作按钮
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                view_btn = st.button("👁️ 查看详情", key=f"view_{task['id']}", use_container_width=True)
            with col2:
                del_btn = st.button("🗑️ 删除", key=f"del_{task['id']}", use_container_width=True)

            if view_btn:
                st.session_state.viewing_task_id = task["id"]
                st.rerun()

            if del_btn:
                if delete_task(task["id"]):
                    if st.session_state.viewing_task_id == task["id"]:
                        st.session_state.viewing_task_id = None
                    st.success(f"✅ 已删除任务 {task['id']}")
                    st.rerun()
                else:
                    st.error("❌ 删除失败")

            # 如果当前正在查看这个任务，显示详情
            if st.session_state.viewing_task_id == task["id"]:
                detail = get_task_detail(task["id"])
                if detail:
                    st.markdown("---")

                    # 筛选和导出
                    col_filter, col_export, col_rest = st.columns([2, 1, 5])

                    with col_filter:
                        # 状态筛选
                        filter_status = st.selectbox(
                            "按状态筛选",
                            options=["全部", "待评估", "优先查看", "约面", "待定", "淘汰"],
                            key=f"filter_status_history_{task['id']}"
                        )

                    with col_export:
                        st.markdown("<br>", unsafe_allow_html=True)
                        # 点按钮才生成文件，不提前生成
                        export_clicked = st.button(
                            "📊 导出 Excel",
                            key=f"export_btn_{task['id']}",
                            use_container_width=True
                        )
                        if export_clicked:
                            export_path = export_candidates_to_excel(detail["candidates"])
                            with open(export_path, "rb") as f:
                                st.download_button(
                                    "⬇️ 下载对比表",
                                    f.read(),
                                    file_name=os.path.basename(export_path),
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_{task['id']}",
                                    use_container_width=True
                                )

                    # 应用筛选
                    filtered_candidates = detail["candidates"]
                    if filter_status != "全部":
                        filtered_candidates = [
                            c for c in filtered_candidates
                            if c.get("status", "") == filter_status
                        ]

                    st.markdown("**📝 JD 内容**")
                    jd_content = detail.get("jd_content", "无")
                    if len(jd_content) > 500:
                        st.caption(jd_content[:500] + "...")
                    else:
                        st.caption(jd_content)
                    st.markdown("---")
                    st.markdown(f"**👥 候选人列表（{len(filtered_candidates)} 人）**")
                    render_candidate_cards(filtered_candidates, editable=True, show_checkboxes=True, checkbox_prefix=f"history_{task['id']}")
                else:
                    st.error("❌ 未找到任务详情")


# ============================================
# 岗位模板标签页
# ============================================
def show_templates_tab():
    """显示岗位模板管理标签页"""
    st.markdown("#### 📋 岗位模板库")
    st.caption("管理常用岗位JD模板，筛选时直接选用，无需重复上传")

    from utils.database import (
        get_template_list, get_template,
        add_template, update_template, delete_template
    )

    # 初始化 session_state
    if 'editing_template_id' not in st.session_state:
        st.session_state.editing_template_id = None

    templates = get_template_list()

    # 统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("模板总数", len(templates))
    with col2:
        builtin_count = len([t for t in templates if t['is_builtin']])
        st.metric("内置模板", builtin_count)
    with col3:
        custom_count = len([t for t in templates if not t['is_builtin']])
        st.metric("自定义模板", custom_count)

    st.markdown("---")

    # 新增模板按钮
    col1, col2 = st.columns([1, 5])
    with col1:
        add_btn = st.button("➕ 新增模板", type="primary", use_container_width=True)

    if add_btn:
        st.session_state.editing_template_id = "new"
        st.rerun()

    # 编辑表单（新增或编辑）
    if st.session_state.editing_template_id:
        is_new = st.session_state.editing_template_id == "new"
        template_data = None

        if not is_new:
            template_data = get_template(st.session_state.editing_template_id)

        with st.form(key="template_form"):
            st.markdown(f"##### {'✨ 新增模板' if is_new else '✏️ 编辑模板'}")

            name = st.text_input(
                "模板名称",
                value=template_data["name"] if template_data else "",
                placeholder="例如：Python高级开发工程师"
            )

            description = st.text_input(
                "模板描述",
                value=template_data["description"] if template_data else "",
                placeholder="简短描述这个模板的用途"
            )

            jd_content = st.text_area(
                "JD 内容",
                value=template_data["jd_content"] if template_data else "",
                height=300,
                placeholder="粘贴完整的岗位描述内容..."
            )

            col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 4])
            with col_submit1:
                submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
            with col_submit2:
                cancel_btn = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                if not name.strip():
                    st.error("❌ 模板名称不能为空")
                elif not jd_content.strip():
                    st.error("❌ JD内容不能为空")
                else:
                    if is_new:
                        new_id = add_template(name.strip(), jd_content, description.strip())
                        if new_id:
                            st.success("✅ 模板添加成功！")
                            st.session_state.editing_template_id = None
                            st.rerun()
                        else:
                            st.error("❌ 添加失败")
                    else:
                        success = update_template(
                            st.session_state.editing_template_id,
                            name.strip(),
                            jd_content,
                            description.strip()
                        )
                        if success:
                            st.success("✅ 模板更新成功！")
                            st.session_state.editing_template_id = None
                            st.rerun()
                        else:
                            st.error("❌ 更新失败")

            if cancel_btn:
                st.session_state.editing_template_id = None
                st.rerun()

        st.markdown("---")

    # 模板列表
    st.markdown("##### 📂 模板列表")

    if not templates:
        st.info("暂无模板，点击「新增模板」创建第一个模板吧！")
        return

    for template in templates:
        is_builtin = template["is_builtin"] == 1
        builtin_tag = " [内置]" if is_builtin else ""

        with st.expander(
            f"  📝 {template['name']}{builtin_tag}    ·    {template.get('description', '无描述')}",
            expanded=False
        ):
            # 模板信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("模板 ID", template["id"])
            with col2:
                st.metric("类型", "内置" if is_builtin else "自定义")
            with col3:
                st.metric("更新时间", template["updated_at"])
            with col4:
                st.metric("创建时间", template["created_at"])

            # 操作按钮
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 3])

            with col_btn1:
                view_btn = st.button("👁️ 预览", key=f"view_tpl_{template['id']}", use_container_width=True)
            with col_btn2:
                edit_btn = st.button(
                    "✏️ 编辑",
                    key=f"edit_tpl_{template['id']}",
                    use_container_width=True,
                    disabled=is_builtin,
                    help="内置模板不可编辑" if is_builtin else "编辑模板"
                )
            with col_btn3:
                del_btn = st.button(
                    "🗑️ 删除",
                    key=f"del_tpl_{template['id']}",
                    use_container_width=True,
                    disabled=is_builtin,
                    help="内置模板不可删除" if is_builtin else "删除模板"
                )

            if edit_btn:
                st.session_state.editing_template_id = template["id"]
                st.rerun()

            if del_btn:
                success = delete_template(template["id"])
                if success:
                    st.success("✅ 模板已删除")
                    st.rerun()
                else:
                    st.error("❌ 删除失败")

            # 预览JD内容
            if view_btn or st.session_state.get(f'previewing_{template["id"]}', False):
                st.session_state[f'previewing_{template["id"]}'] = True
                st.markdown("**📄 JD 内容预览**")
                st.text_area(
                    "",
                    value=template.get("jd_content", ""),
                    height=300,
                    disabled=True,
                    key=f"preview_content_{template['id']}"
                )


if __name__ == "__main__":
    import subprocess
    import sys
    import os

    def _is_running_in_streamlit():
        """检测当前是否在Streamlit运行时环境中"""
        # 1. 环境变量检测
        if os.environ.get("STREAMLIT_LAUNCHED") == "1":
            return True
        if os.environ.get("STREAMLIT_SERVER_HEADLESS") is not None:
            return True
        if os.environ.get("STREAMLIT_SERVER_PORT") is not None:
            return True
        # 2. 运行时上下文检测（最可靠）
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            if get_script_run_ctx() is not None:
                return True
        except Exception:
            pass
        return False

    if _is_running_in_streamlit():
        # 已经在Streamlit环境中（包括Streamlit Cloud），直接运行主程序
        main()
    else:
        # 本地直接运行 python app.py，自动启动streamlit
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)

        print("=" * 50)
        print("  候选人初筛助手 启动中...")
        print("=" * 50)
        print(f"  项目目录: {current_dir}")
        print("  浏览器将自动打开")
        print("  按 Ctrl+C 停止服务")
        print("=" * 50)
        print()

        env = os.environ.copy()
        env["STREAMLIT_LAUNCHED"] = "1"

        try:
            subprocess.run(
                [sys.executable, "-m", "streamlit", "run", current_file,
                 "--server.headless=false",
                 "--browser.gatherUsageStats=false"],
                cwd=current_dir,
                env=env
            )
        except KeyboardInterrupt:
            print("\n服务已停止")
