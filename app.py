import streamlit as st
from datetime import datetime, timedelta
import os
from config import Config
from search_engines import search_manager
from qwen_client import qwen_client
from download_manager import download_manager
from download_history import download_history


# 页面配置
st.set_page_config(
    page_title="学术文献检索Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .paper-card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
        background-color: #f9f9f9;
    }
    .paper-title {
        font-size: 18px;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 10px;
    }
    .paper-meta {
        font-size: 14px;
        color: #666;
        margin-bottom: 10px;
    }
    .paper-abstract {
        font-size: 14px;
        line-height: 1.6;
        margin-top: 10px;
    }
    .translation {
        background-color: #f0f8ff;
        color: #2c3e50;
        padding: 12px;
        border-radius: 8px;
        margin-top: 10px;
        border-left: 4px solid #3498db;
        font-size: 14px;
        line-height: 1.6;
    }
    .translation strong {
        color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化session state"""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_papers' not in st.session_state:
        st.session_state.selected_papers = set()
    if 'translations' not in st.session_state:
        st.session_state.translations = {}


def validate_config():
    """验证配置"""
    try:
        Config.validate()
        return True
    except ValueError as e:
        st.error(f"❌ 配置错误: {str(e)}")
        st.info("请在项目根目录创建 .env 文件并配置 QWEN_API_KEY")
        return False


def perform_search(keywords, start_date, end_date, sources):
    """执行搜索"""
    with st.spinner('🔍 正在搜索文献...'):
        results = search_manager.search_all(
            keywords=keywords,
            start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
            end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
            sources=sources
        )
        st.session_state.search_results = results
        st.session_state.selected_papers = set()
        st.session_state.translations = {}
    return results


def translate_text(text, cache_key, auto=False):
    """翻译文本（带缓存）"""
    if cache_key not in st.session_state.translations:
        if not auto:
            with st.spinner('🌐 正在翻译...'):
                translation = qwen_client.translate_to_chinese(text)
                st.session_state.translations[cache_key] = translation
        else:
            # 自动翻译（后台静默翻译）
            translation = qwen_client.translate_to_chinese(text)
            st.session_state.translations[cache_key] = translation
    return st.session_state.translations.get(cache_key)


def auto_translate_papers(papers):
    """自动翻译论文标题和摘要"""
    if not Config.AUTO_TRANSLATE:
        return
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    total = len(papers)
    for idx, paper in enumerate(papers):
        paper_dict = paper.to_dict()
        paper_id_base = f"{idx}_{paper_dict['title'][:50]}"
        
        # 翻译标题
        title_key = f"title_{paper_id_base}"
        if title_key not in st.session_state.translations:
            translate_text(paper_dict['title'], title_key, auto=True)
        
        # 翻译摘要（可选，摘要较长可能消耗较多配额）
        abstract_key = f"abstract_{paper_id_base}"
        if abstract_key not in st.session_state.translations:
            translate_text(paper_dict['abstract'], abstract_key, auto=True)
        
        # 更新进度
        progress = (idx + 1) / total
        progress_bar.progress(progress)
        progress_text.text(f"正在翻译论文 {idx + 1}/{total}...")
    
    progress_bar.empty()
    progress_text.empty()


def display_paper(paper, index):
    """显示单篇论文"""
    paper_dict = paper.to_dict()
    
    # 创建唯一标识
    paper_id = f"{index}_{paper_dict['title'][:50]}"
    
    # 检查是否已下载
    is_downloaded = download_history.is_downloaded(paper_dict['title'])
    download_info = download_history.get_download_info(paper_dict['title']) if is_downloaded else None
    
    # 勾选框
    col1, col2 = st.columns([0.05, 0.95])
    with col1:
        # 如果已下载，禁用勾选框
        if is_downloaded:
            st.checkbox(
                "选择",
                key=f"select_{paper_id}",
                value=False,
                disabled=True,
                label_visibility="collapsed"
            )
        else:
            is_selected = st.checkbox(
                "选择",
                key=f"select_{paper_id}",
                value=paper_id in st.session_state.selected_papers,
                label_visibility="collapsed"
            )
            if is_selected:
                st.session_state.selected_papers.add(paper_id)
            elif paper_id in st.session_state.selected_papers:
                st.session_state.selected_papers.remove(paper_id)
    
    with col2:
        # 标题（英文）+ 已下载标记
        if is_downloaded:
            st.markdown(f"### 📄 {paper_dict['title']} ✅")
            st.markdown(f'<div style="background-color: #d4edda; color: #155724; padding: 8px; border-radius: 5px; margin-bottom: 10px; font-size: 13px;">📥 已下载 | 日期: {download_info["date_only"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"### 📄 {paper_dict['title']}")
        
        # 显示中文标题（如果已翻译或点击翻译按钮）
        title_key = f"title_{paper_id}"
        title_translation = st.session_state.translations.get(title_key)
        
        if title_translation:
            st.markdown(f'<div class="translation"><strong>中文标题:</strong> {title_translation}</div>', 
                       unsafe_allow_html=True)
        elif not Config.AUTO_TRANSLATE:
            # 如果未开启自动翻译，显示翻译按钮
            if st.button("🌐 翻译标题", key=f"trans_title_btn_{paper_id}"):
                translation = translate_text(paper_dict['title'], title_key, auto=False)
                if translation:
                    st.rerun()
        
        # 元信息
        meta_info = []
        if paper_dict['source']:
            meta_info.append(f"📚 来源: {paper_dict['source']}")
        if paper_dict['published']:
            meta_info.append(f"📅 发表日期: {paper_dict['published']}")
        if paper_dict['authors']:
            authors_str = ", ".join(paper_dict['authors'][:3])
            if len(paper_dict['authors']) > 3:
                authors_str += f" 等 {len(paper_dict['authors'])} 位作者"
            meta_info.append(f"✍️ 作者: {authors_str}")
        
        if meta_info:
            st.markdown(" | ".join(meta_info))
        
        # 链接
        col_link1, col_link2 = st.columns(2)
        with col_link1:
            if paper_dict['url']:
                st.markdown(f"🔗 [查看论文]({paper_dict['url']})")
        with col_link2:
            if paper_dict['pdf_url']:
                st.markdown(f"📥 [PDF链接]({paper_dict['pdf_url']})")
        
        # 摘要
        with st.expander("查看摘要", expanded=False):
            st.markdown(f"**English Abstract:** {paper_dict['abstract']}")
            
            # 显示中文摘要（如果已翻译或点击翻译按钮）
            abstract_key = f"abstract_{paper_id}"
            abstract_translation = st.session_state.translations.get(abstract_key)
            
            if abstract_translation:
                st.markdown("**中文摘要:**")
                st.markdown(f'<div class="translation">{abstract_translation}</div>', 
                          unsafe_allow_html=True)
            elif not Config.AUTO_TRANSLATE:
                # 如果未开启自动翻译，显示翻译按钮
                if st.button("🌐 翻译摘要", key=f"trans_abs_btn_{paper_id}"):
                    translation = translate_text(paper_dict['abstract'], abstract_key, auto=False)
                    if translation:
                        st.rerun()
        
        st.divider()
    
    return paper_dict, paper_id


def download_selected_papers():
    """下载选中的论文"""
    if not st.session_state.selected_papers:
        st.warning("⚠️ 请先选择要下载的论文")
        return
    
    # 获取选中的论文
    selected_indices = []
    for paper_id in st.session_state.selected_papers:
        try:
            idx = int(paper_id.split('_')[0])
            selected_indices.append(idx)
        except:
            continue
    
    papers_to_download = [
        st.session_state.search_results[idx].to_dict() 
        for idx in selected_indices 
        if idx < len(st.session_state.search_results)
    ]
    
    # 过滤掉没有PDF链接的论文
    papers_with_pdf = [p for p in papers_to_download if p.get('pdf_url')]
    
    if not papers_with_pdf:
        st.error("❌ 选中的论文都没有可用的PDF链接")
        return
    
    # 显示下载进度
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(current, total):
        progress = (current + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"正在下载: {current + 1}/{total}")
    
    # 执行下载
    results = download_manager.download_multiple(
        papers_with_pdf,
        progress_callback=update_progress
    )
    
    # 显示结果
    progress_bar.empty()
    status_text.empty()
    
    # 显示下载统计
    total_success = len(results['success'])
    total_skipped = len(results.get('skipped', []))
    total_failed = len(results['failed'])
    
    if total_success > 0:
        st.success(f"✅ 成功下载 {total_success} 篇论文")
    
    if total_skipped > 0:
        st.info(f"ℹ️ 跳过 {total_skipped} 篇已下载的论文")
        with st.expander("查看跳过的论文"):
            for item in results['skipped']:
                st.text(f"- {item['title']}: {item['message']}")
    
    if total_failed > 0:
        st.warning(f"⚠️ {total_failed} 篇论文下载失败")
        with st.expander("查看失败详情"):
            for item in results['failed']:
                st.text(f"- {item['title']}: {item['message']}")
    
    st.info(f"📁 下载位置: {download_manager.get_download_path()}")
    st.info(f"📊 历史统计: 累计下载 {download_history.get_total_downloads()} 篇论文")


def main():
    """主函数"""
    # 初始化
    init_session_state()
    
    # 标题
    st.title("📚 学术文献检索Agent")
    st.markdown("基于Qwen API的智能文献检索和下载工具")
    
    # 验证配置
    if not validate_config():
        return
    
    # 侧边栏 - 搜索配置
    with st.sidebar:
        st.header("🔧 搜索设置")
        
        # 关键词输入
        keywords = st.text_input(
            "搜索关键词",
            placeholder="例如: machine learning, neural networks",
            help="输入要搜索的关键词"
        )
        
        # 日期范围
        st.subheader("📅 日期范围")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=datetime.now() - timedelta(days=3),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.now(),
                max_value=datetime.now()
            )
        
        # 数据源选择
        st.subheader("📖 数据源")
        sources = []
        if st.checkbox("ArXiv", value=True):
            sources.append('arxiv')
        if st.checkbox("OpenReview", value=True):
            sources.append('openreview')
        if st.checkbox("Google Scholar", value=False):
            sources.append('google_scholar')
        
        # 高级设置
        st.subheader("⚙️ 高级设置")
        
        # 最大结果数
        max_results = st.slider(
            "最大搜索结果数",
            min_value=10,
            max_value=200,
            value=Config.MAX_RESULTS,
            step=10,
            help="每次搜索返回的最大论文数量"
        )
        Config.MAX_RESULTS = max_results
        
        # 自动翻译开关
        auto_translate = st.toggle(
            "自动翻译标题和摘要",
            value=Config.AUTO_TRANSLATE,
            help="开启后搜索完成自动翻译所有论文，关闭后需手动点击翻译按钮"
        )
        Config.AUTO_TRANSLATE = auto_translate
        
        # 下载路径设置
        st.subheader("📁 下载设置")
        custom_path = st.text_input(
            "下载路径",
            value=download_manager.get_download_path(),
            help="论文PDF的保存路径"
        )
        if custom_path != download_manager.get_download_path():
            download_manager.set_download_path(custom_path)
        
        # 下载历史管理
        st.subheader("📊 下载历史")
        total_downloads = download_history.get_total_downloads()
        st.write(f"累计下载: **{total_downloads}** 篇论文")
        
        if total_downloads > 0:
            if st.button("🗑️ 清空历史记录", use_container_width=True):
                download_history.clear_history()
                st.success("历史记录已清空")
                st.rerun()
        
        # 搜索按钮
        st.markdown("---")
        search_button = st.button("🔍 开始搜索", type="primary", use_container_width=True)
    
    # 主界面
    if search_button:
        if not keywords:
            st.warning("⚠️ 请输入搜索关键词")
        elif not sources:
            st.warning("⚠️ 请至少选择一个数据源")
        else:
            results = perform_search(keywords, start_date, end_date, sources)
            
            if results:
                st.success(f"✅ 找到 {len(results)} 篇相关论文")
                # 自动翻译所有论文
                if Config.AUTO_TRANSLATE:
                    with st.spinner('🌐 正在自动翻译论文...'):
                        auto_translate_papers(results)
                    st.success("✨ 翻译完成！")
            else:
                st.info("ℹ️ 未找到相关论文，请尝试其他关键词")
    
    # 显示搜索结果
    if st.session_state.search_results:
        st.header("📑 搜索结果")
        
        # 显示搜索配置信息
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"📊 搜索到 {len(st.session_state.search_results)} 篇论文")
        with col_info2:
            translate_status = "✅ 已开启" if Config.AUTO_TRANSLATE else "❌ 已关闭"
            st.caption(f"🌐 自动翻译: {translate_status}")
        
        # 操作按钮
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("✅ 全选"):
                for idx, paper in enumerate(st.session_state.search_results):
                    paper_dict = paper.to_dict()
                    paper_id = f"{idx}_{paper_dict['title'][:50]}"
                    st.session_state.selected_papers.add(paper_id)
                st.rerun()
        
        with col2:
            if st.button("❌ 取消全选"):
                st.session_state.selected_papers.clear()
                st.rerun()
        
        st.markdown(f"**已选择: {len(st.session_state.selected_papers)} 篇论文**")
        
        # 显示每篇论文
        for idx, paper in enumerate(st.session_state.search_results):
            display_paper(paper, idx)
        
        # 下载按钮
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("📥 下载选中论文", type="primary", use_container_width=True):
                download_selected_papers()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Powered by Qwen API | 学术文献检索Agent"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
