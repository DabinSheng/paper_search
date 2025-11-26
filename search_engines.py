import arxiv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
from config import Config


class Paper:
    """论文数据类"""
    
    def __init__(self, title: str, abstract: str, url: str, pdf_url: Optional[str] = None,
                 authors: List[str] = None, published: Optional[str] = None, source: str = ""):
        self.title = title
        self.abstract = abstract
        self.url = url
        self.pdf_url = pdf_url
        self.authors = authors or []
        self.published = published
        self.source = source
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'title': self.title,
            'abstract': self.abstract,
            'url': self.url,
            'pdf_url': self.pdf_url,
            'authors': self.authors,
            'published': self.published,
            'source': self.source
        }


class SearchEngine:
    """学术搜索引擎基类"""
    
    def __init__(self):
        # 不在初始化时固定max_results，改为每次搜索时动态获取
        pass
    
    @property
    def max_results(self):
        """动态获取最大结果数"""
        from config import Config
        return Config.MAX_RESULTS
        
    def search(self, keywords: str, start_date: Optional[str] = None, 
               end_date: Optional[str] = None) -> List[Paper]:
        """搜索论文"""
        raise NotImplementedError


class ArxivSearchEngine(SearchEngine):
    """ArXiv搜索引擎"""
    
    def search(self, keywords: str, start_date: Optional[str] = None, 
               end_date: Optional[str] = None) -> List[Paper]:
        """
        在ArXiv上搜索论文
        
        Args:
            keywords: 搜索关键词
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            论文列表
        """
        papers = []
        
        try:
            # 构建查询
            query = keywords
            
            # 创建搜索客户端
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            # 执行搜索
            for result in client.results(search):
                # 检查日期范围
                published_date = result.published.strftime('%Y-%m-%d')
                
                if start_date and published_date < start_date:
                    continue
                if end_date and published_date > end_date:
                    continue
                
                paper = Paper(
                    title=result.title,
                    abstract=result.summary,
                    url=result.entry_id,
                    pdf_url=result.pdf_url,
                    authors=[author.name for author in result.authors],
                    published=published_date,
                    source="ArXiv"
                )
                papers.append(paper)
                
        except Exception as e:
            print(f"ArXiv搜索出错: {str(e)}")
            
        return papers


class OpenReviewSearchEngine(SearchEngine):
    """OpenReview搜索引擎"""
    
    def search(self, keywords: str, start_date: Optional[str] = None, 
               end_date: Optional[str] = None) -> List[Paper]:
        """
        在OpenReview上搜索论文
        
        Args:
            keywords: 搜索关键词
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            论文列表
        """
        papers = []
        
        try:
            # OpenReview V2 搜索API
            url = "https://api2.openreview.net/notes/search"
            params = {
                'term': keywords,
                'limit': min(self.max_results, 100),
                'offset': 0
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                notes = data.get('notes', [])
                
                for note in notes[:self.max_results]:
                    content = note.get('content', {})
                    
                    # 提取日期 (V2 API格式)
                    cdate = note.get('cdate', 0)
                    if cdate:
                        published_date = datetime.fromtimestamp(cdate / 1000).strftime('%Y-%m-%d')
                    else:
                        published_date = None
                    
                    # 检查日期范围
                    if published_date:
                        if start_date and published_date < start_date:
                            continue
                        if end_date and published_date > end_date:
                            continue
                    
                    # V2 API的content结构不同，字段可能是对象
                    def get_value(field):
                        """从V2 API的字段中提取值"""
                        if isinstance(field, dict):
                            return field.get('value', '')
                        return field if field else ''
                    
                    title = get_value(content.get('title', ''))
                    if not title or title == 'No Title':
                        # 跳过没有标题的论文（通常是评论或其他非正式内容）
                        continue
                    
                    abstract = get_value(content.get('abstract', ''))
                    if not abstract:
                        # 尝试从其他字段获取摘要
                        abstract = get_value(content.get('summary', ''))
                    if not abstract:
                        abstract = 'No Abstract'
                    
                    authors = content.get('authors', [])
                    if isinstance(authors, dict):
                        authors = authors.get('value', [])
                    if not isinstance(authors, list):
                        authors = []
                    
                    note_id = note.get('id', '')
                    
                    paper = Paper(
                        title=title,
                        abstract=abstract,
                        url=f"https://openreview.net/forum?id={note_id}",
                        pdf_url=f"https://openreview.net/pdf?id={note_id}",
                        authors=authors,
                        published=published_date,
                        source="OpenReview"
                    )
                    papers.append(paper)
            else:
                print(f"OpenReview API响应错误: {response.status_code}")
                    
        except Exception as e:
            print(f"OpenReview搜索出错: {str(e)}")
            
        return papers


class GoogleScholarSearchEngine(SearchEngine):
    """Google Scholar搜索引擎 (简化版，使用爬虫)"""
    
    def search(self, keywords: str, start_date: Optional[str] = None, 
               end_date: Optional[str] = None) -> List[Paper]:
        """
        在Google Scholar上搜索论文
        注意：这是简化实现，实际使用可能需要更复杂的爬虫或API
        
        Args:
            keywords: 搜索关键词
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            论文列表
        """
        papers = []
        
        try:
            # 构建搜索URL
            base_url = "https://scholar.google.com/scholar"
            params = {
                'q': keywords,
                'hl': 'en',
                'as_sdt': '0,5'
            }
            
            # 添加日期范围
            if start_date:
                params['as_ylo'] = start_date[:4]
            if end_date:
                params['as_yhi'] = end_date[:4]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_='gs_ri')
                
                for result in results[:min(len(results), self.max_results)]:
                    title_elem = result.find('h3', class_='gs_rt')
                    if not title_elem:
                        continue
                        
                    # 提取标题和链接
                    title = title_elem.get_text()
                    link_elem = title_elem.find('a')
                    url = link_elem['href'] if link_elem else ''
                    
                    # 提取摘要
                    abstract_elem = result.find('div', class_='gs_rs')
                    abstract = abstract_elem.get_text() if abstract_elem else ''
                    
                    # 提取作者和发表信息
                    authors_elem = result.find('div', class_='gs_a')
                    authors_text = authors_elem.get_text() if authors_elem else ''
                    
                    paper = Paper(
                        title=title.strip(),
                        abstract=abstract.strip(),
                        url=url,
                        pdf_url=None,  # Google Scholar不直接提供PDF链接
                        authors=[],
                        published=None,
                        source="Google Scholar"
                    )
                    papers.append(paper)
                    
                # 避免过于频繁的请求
                time.sleep(2)
                
        except Exception as e:
            print(f"Google Scholar搜索出错: {str(e)}")
            
        return papers


class SearchManager:
    """搜索管理器，统一管理多个搜索引擎"""
    
    def __init__(self):
        self.engines = {
            'arxiv': ArxivSearchEngine(),
            'openreview': OpenReviewSearchEngine(),
            'google_scholar': GoogleScholarSearchEngine()
        }
        
    def search_all(self, keywords: str, start_date: Optional[str] = None,
                   end_date: Optional[str] = None, sources: List[str] = None) -> List[Paper]:
        """
        在所有选定的搜索引擎上搜索
        
        Args:
            keywords: 搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            sources: 要搜索的来源列表，默认全部
            
        Returns:
            所有搜索结果的合并列表
        """
        if sources is None:
            sources = list(self.engines.keys())
            
        all_papers = []
        
        for source in sources:
            if source in self.engines:
                print(f"正在搜索 {source}...")
                papers = self.engines[source].search(keywords, start_date, end_date)
                all_papers.extend(papers)
                print(f"从 {source} 找到 {len(papers)} 篇论文")
                
        return all_papers


# 创建全局搜索管理器实例
search_manager = SearchManager()
