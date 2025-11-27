#!/usr/bin/env python3
"""测试Google Scholar解析改进"""

from search_engines import GoogleScholarSearchEngine

def test_scholar_search():
    """测试Google Scholar搜索和解析"""
    engine = GoogleScholarSearchEngine()
    
    # 测试关键词
    keywords = "deep learning"
    print(f"🔍 测试搜索: {keywords}\n")
    
    # 执行搜索（只获取5篇作为测试）
    from config import Config
    original_max = Config.MAX_RESULTS
    Config.MAX_RESULTS = 5  # 临时设置为5
    
    try:
        papers = engine.search(keywords)
        
        print(f"\n📊 搜索结果统计:")
        print(f"总共找到: {len(papers)} 篇论文\n")
        
        for idx, paper in enumerate(papers, 1):
            print(f"{'='*60}")
            print(f"论文 {idx}:")
            print(f"标题: {paper.title}")
            print(f"摘要长度: {len(paper.abstract)} 字符")
            print(f"摘要预览: {paper.abstract[:150]}...")
            print(f"URL: {paper.url}")
            print(f"PDF: {paper.pdf_url if paper.pdf_url else '❌ 无PDF链接'}")
            print(f"作者: {', '.join(paper.authors) if paper.authors else '未提取到作者'}")
            print()
        
        # 统计
        with_pdf = sum(1 for p in papers if p.pdf_url)
        with_abstract = sum(1 for p in papers if len(p.abstract) > 100)
        
        print(f"\n📈 质量统计:")
        print(f"  有PDF链接: {with_pdf}/{len(papers)} ({with_pdf/len(papers)*100:.1f}%)")
        print(f"  完整摘要: {with_abstract}/{len(papers)} ({with_abstract/len(papers)*100:.1f}%)")
        
    finally:
        Config.MAX_RESULTS = original_max

if __name__ == "__main__":
    test_scholar_search()
