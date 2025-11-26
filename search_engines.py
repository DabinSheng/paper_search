import arxiv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
import random
from config import Config

# Selenium支持（可选）
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


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
    """Google Scholar搜索引擎（Selenium优先，带重试机制）"""
    
    def __init__(self):
        super().__init__()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.use_selenium = SELENIUM_AVAILABLE
    
    def search(self, keywords: str, start_date: Optional[str] = None, 
               end_date: Optional[str] = None) -> List[Paper]:
        """搜索论文（优先使用Selenium）"""
        papers = []
        
        # 优先使用Selenium
        if self.use_selenium and SELENIUM_AVAILABLE:
            print("🚀 使用Selenium浏览器模拟搜索...")
            papers = self._search_with_selenium(keywords, start_date, end_date)
            if papers:
                return papers
            print("⚠️ Selenium搜索失败")
        else:
            print("⚠️ Selenium不可用，请安装: pip install selenium webdriver-manager")
            print("💡 或者使用ArXiv和OpenReview作为替代数据源")
        
        return papers
    
    def _search_with_selenium(self, keywords: str, 
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> List[Paper]:
        """使用Selenium模拟浏览器搜索"""
        papers = []
        driver = None
        
        try:
            print("📦 正在初始化浏览器...")
            
            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # 新版无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument(f'user-agent={random.choice(self.user_agents)}')
            
            # 反检测设置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 代理设置（如果需要，取消注释）
            # chrome_options.add_argument('--proxy-server=http://127.0.0.1:7890')
            
            # 初始化浏览器
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"⚠️ ChromeDriver初始化失败: {str(e)}")
                print("💡 尝试使用系统Chrome...")
                driver = webdriver.Chrome(options=chrome_options)
            
            # 设置脚本防止被检测为自动化
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            driver.set_page_load_timeout(30)
            
            # 构建URL
            query = keywords.replace(" ", "+")
            url = f"https://scholar.google.com/scholar?q={query}&hl=zh-CN&num={min(20, self.max_results)}"
            
            if start_date:
                url += f"&as_ylo={start_date[:4]}"
            if end_date:
                url += f"&as_yhi={end_date[:4]}"
            
            print(f"🔍 正在访问: {url[:80]}...")
            
            # 访问页面
            driver.get(url)
            
            # 等待页面加载
            time.sleep(random.uniform(3, 5))
            
            # 检查是否被拦截
            page_source = driver.page_source.lower()
            
            if 'sorry' in page_source or 'unusual traffic' in page_source:
                print("⚠️ Google检测到异常流量，需要验证")
                print("💡 解决方案：")
                print("   1. 等待10-15分钟后重试")
                print("   2. 使用VPN/代理（取消代码中的proxy-server注释）")
                print("   3. 临时使用ArXiv和OpenReview")
                return papers
            
            if 'captcha' in page_source:
                print("⚠️ 检测到验证码")
                print("💡 建议启用有头模式（注释掉--headless）手动完成验证")
                return papers
            
            # 获取页面源码
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 解析结果
            results = soup.find_all(class_="gs_ri")
            
            if not results:
                print("⚠️ 未找到搜索结果")
                # 保存HTML用于调试
                # with open('debug_scholar.html', 'w', encoding='utf-8') as f:
                #     f.write(html)
                return papers
            
            print(f"📄 找到 {len(results)} 个搜索结果，开始解析...")
            
            for idx, result in enumerate(results[:min(len(results), self.max_results)], 1):
                try:
                    title_elem = result.find('h3')
                    if not title_elem:
                        continue
                    
                    paper = Paper(
                        title="",
                        abstract="",
                        url="",
                        pdf_url=None,
                        authors=[],
                        published=None,
                        source="Google Scholar"
                    )
                    
                    # 标题
                    paper.title = title_elem.get_text().strip()
                    paper.title = paper.title.replace('[HTML]', '').replace('[PDF]', '').replace('[图书]', '').strip()
                    
                    # 链接
                    link = title_elem.find('a')
                    if link and link.has_attr('href'):
                        paper.url = link.get('href')
                    
                    # 摘要
                    abstract_elem = result.find(class_="gs_rs")
                    if abstract_elem:
                        paper.abstract = abstract_elem.get_text().strip()
                    else:
                        paper.abstract = "摘要不可用"
                    
                    # 期刊/作者
                    journal_elem = result.find(class_="gs_a")
                    if journal_elem:
                        paper.published = journal_elem.get_text()
                    
                    # 尝试提取PDF链接
                    pdf_links = result.find_all('a', href=True)
                    for link in pdf_links:
                        href = link.get('href', '')
                        if '.pdf' in href.lower() and href.startswith('http'):
                            paper.pdf_url = href
                            break
                    
                    papers.append(paper)
                    
                except Exception as e:
                    print(f"⚠️ 解析第{idx}篇论文时出错: {str(e)}")
                    continue
            
            if papers:
                print(f"✅ 成功获取 {len(papers)} 篇论文")
            else:
                print("⚠️ 未能解析出任何论文")
            
        except Exception as e:
            print(f"⚠️ Selenium搜索出错: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
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
