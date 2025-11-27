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
            # chrome_options.add_argument('--headless=new')  # 注释掉无头模式，启用可视化浏览器
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
            chrome_options.add_argument('--proxy-server=http://127.0.0.1:7890')
            
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
                print("⚠️ Google检测到异常流量，需要人工验证")
                print("🌐 浏览器窗口已打开，请手动完成验证...")
                print("⏳ 等待用户完成验证（最多120秒）...")
                
                # 等待用户完成验证（检查URL是否改变或页面内容是否改变）
                max_wait = 120  # 最多等待120秒
                start_time = time.time()
                verified = False
                
                while time.time() - start_time < max_wait:
                    try:
                        current_source = driver.page_source.lower()
                        # 检查是否已经通过验证（验证页面消失）
                        if 'sorry' not in current_source and 'unusual traffic' not in current_source:
                            if 'scholar' in driver.current_url and 'gs_ri' in driver.page_source:
                                print("✅ 验证成功！继续搜索...")
                                verified = True
                                break
                        time.sleep(2)  # 每2秒检查一次
                    except:
                        pass
                
                if not verified:
                    print("⏰ 验证超时，请稍后重试")
                    return papers
                
                # 验证成功后重新获取页面内容
                time.sleep(2)
                page_source = driver.page_source.lower()
            
            if 'captcha' in page_source and 'gs_ri' not in driver.page_source:
                print("⚠️ 检测到验证码，需要人工验证")
                print("🌐 浏览器窗口已打开，请手动完成验证...")
                print("⏳ 等待用户完成验证（最多120秒）...")
                
                # 等待验证码完成
                max_wait = 120
                start_time = time.time()
                verified = False
                
                while time.time() - start_time < max_wait:
                    try:
                        current_source = driver.page_source.lower()
                        # 检查是否已有搜索结果
                        if 'gs_ri' in driver.page_source and 'captcha' not in current_source:
                            print("✅ 验证成功！继续搜索...")
                            verified = True
                            break
                        time.sleep(2)
                    except:
                        pass
                
                if not verified:
                    print("⏰ 验证超时，请稍后重试")
                    return papers
                
                # 验证成功后重新获取页面内容
                time.sleep(2)
            
            # 获取页面源码
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 尝试点击"更多"按钮展开所有摘要
            try:
                # 查找并点击所有"显示更多"按钮
                show_more_buttons = driver.find_elements(By.CLASS_NAME, 'gs_rs')
                for button_elem in show_more_buttons[:5]:  # 只展开前5个避免超时
                    try:
                        # 检查是否有"..."表示被截断
                        if '...' in button_elem.text:
                            # 尝试点击展开
                            driver.execute_script("arguments[0].click();", button_elem)
                            time.sleep(0.5)
                    except:
                        pass
                
                # 重新获取页面内容
                time.sleep(1)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
            except Exception as e:
                print(f"  ℹ️ 无法展开摘要: {str(e)}")
            
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
                    
                    # 摘要 - 获取完整摘要（包括被隐藏的部分）
                    abstract_elem = result.find(class_="gs_rs")
                    if abstract_elem:
                        # 获取所有文本，包括可能被折叠的内容
                        full_abstract = abstract_elem.get_text(separator=' ', strip=True)
                        paper.abstract = full_abstract
                        
                        # 如果摘要以"..."结尾，说明被截断了
                        if paper.abstract.endswith('...') or len(paper.abstract) < 150:
                            # 对于arXiv论文，直接从arXiv获取完整摘要
                            if paper.url and 'arxiv.org' in paper.url:
                                print(f"  🔄 论文{idx}摘要被截断，从arXiv获取完整版...")
                                enhanced_abstract = self._fetch_full_abstract(paper.url, driver)
                                if enhanced_abstract and len(enhanced_abstract) > len(paper.abstract):
                                    paper.abstract = enhanced_abstract
                                    print(f"  ✅ 获取到完整摘要: {len(paper.abstract)} 字符")
                        
                        print(f"  📝 论文{idx}摘要: {paper.abstract[:100]}{'...' if len(paper.abstract) > 100 else ''}")
                    else:
                        paper.abstract = "摘要不可用"
                    
                    # 作者和出版信息
                    authors_elem = result.find(class_="gs_a")
                    if authors_elem:
                        author_info = authors_elem.get_text().strip()
                        paper.published = author_info
                        # 尝试提取作者名称
                        if ' - ' in author_info:
                            authors_part = author_info.split(' - ')[0]
                            paper.authors = [a.strip() for a in authors_part.split(',')]
                    
                    # 提取PDF链接 - 改进策略
                    # 1. 首先查找右侧的PDF链接（通常在gs_or_ggsm类中）
                    pdf_link_elem = result.find_parent(class_='gs_r').find(class_='gs_or_ggsm') if result.find_parent(class_='gs_r') else None
                    if pdf_link_elem:
                        pdf_a = pdf_link_elem.find('a', href=True)
                        if pdf_a and pdf_a.get('href'):
                            href = pdf_a.get('href')
                            if href.startswith('http'):
                                paper.pdf_url = href
                    
                    # 2. 如果没找到，尝试在结果中查找所有包含PDF的链接
                    if not paper.pdf_url:
                        all_links = result.find_parent(class_='gs_r').find_all('a', href=True) if result.find_parent(class_='gs_r') else result.find_all('a', href=True)
                        for link_elem in all_links:
                            href = link_elem.get('href', '')
                            link_text = link_elem.get_text().lower()
                            # 查找明确标注为PDF的链接
                            if ('[pdf]' in link_text or 'pdf' in link_text) and href.startswith('http'):
                                paper.pdf_url = href
                                break
                            # 或者链接直接指向PDF文件
                            elif '.pdf' in href.lower() and href.startswith('http'):
                                paper.pdf_url = href
                                break
                    
                    # 3. 智能PDF查找：如果论文URL是arXiv、Semantic Scholar等，尝试构建PDF链接
                    if not paper.pdf_url and paper.url:
                        paper.pdf_url = self._try_construct_pdf_url(paper.url)
                    
                    # 调试信息
                    pdf_status = "✅" if paper.pdf_url else "❌"
                    print(f"  {pdf_status} 论文{idx}: {paper.title[:50]}...")
                    
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
    
    def _try_construct_pdf_url(self, url: str) -> Optional[str]:
        """尝试从论文URL构建PDF链接"""
        if not url:
            return None
        
        try:
            # arXiv: 将abs链接转换为pdf链接
            if 'arxiv.org/abs/' in url:
                return url.replace('/abs/', '/pdf/') + '.pdf'
            
            # Semantic Scholar
            if 'semanticscholar.org/paper/' in url:
                # Semantic Scholar的PDF需要通过API或重定向获取，这里先返回None
                pass
            
            # ACM Digital Library
            if 'dl.acm.org' in url and '/doi/' in url:
                # ACM的PDF需要订阅，返回None
                pass
            
            # IEEE Xplore
            if 'ieeexplore.ieee.org' in url:
                # IEEE的PDF需要订阅，返回None
                pass
                
        except Exception as e:
            print(f"⚠️ 构建PDF链接失败: {str(e)}")
        
        return None
    
    def _fetch_full_abstract(self, url: str, driver) -> Optional[str]:
        """从论文原始页面获取完整摘要"""
        if not url or not url.startswith('http'):
            return None
        
        try:
            # 对于arXiv链接，使用特殊处理
            if 'arxiv.org/abs/' in url:
                current_window = driver.current_window_handle
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                
                try:
                    driver.get(url)
                    time.sleep(2)
                    
                    # arXiv的摘要在blockquote.abstract元素中
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    abstract_elem = soup.find('blockquote', class_='abstract')
                    if abstract_elem:
                        # 移除"Abstract:"标签
                        abstract_text = abstract_elem.get_text(strip=True)
                        abstract_text = abstract_text.replace('Abstract:', '').strip()
                        return abstract_text
                finally:
                    driver.close()
                    driver.switch_to.window(current_window)
            
            # 对于其他链接，尝试通用方法（限制避免过度请求）
            # 这里我们暂时不处理，避免打开太多页面影响性能
            
        except Exception as e:
            print(f"    ⚠️ 获取完整摘要失败: {str(e)}")
        
        return None


class SearchManager:
    """搜索管理器，统一管理多个搜索引擎"""
    
    def __init__(self):
        self.engines = {
            'arxiv': ArxivSearchEngine(),
            'openreview': OpenReviewSearchEngine(),
            'google_scholar': GoogleScholarSearchEngine()
        }
    
    def _filter_paper(self, paper: Paper, exclude_keywords: list, require_keywords: list) -> bool:
        """智能过滤论文
        
        Args:
            paper: 论文对象
            exclude_keywords: 排除关键词列表
            require_keywords: 必需关键词列表
            
        Returns:
            True表示保留，False表示过滤掉
        """
        # 合并标题和摘要用于检查
        content = (paper.title + ' ' + paper.abstract).lower()
        
        # 检查排除关键词
        if exclude_keywords:
            for keyword in exclude_keywords:
                if keyword.lower() in content:
                    print(f"  🚫 过滤掉: {paper.title[:60]}... (包含排除词: {keyword})")
                    return False
        
        # 检查必需关键词
        if require_keywords:
            has_required = False
            for keyword in require_keywords:
                if keyword.lower() in content:
                    has_required = True
                    break
            if not has_required:
                print(f"  🚫 过滤掉: {paper.title[:60]}... (缺少必需关键词)")
                return False
        
        return True
        
    def search_all(self, keywords: str, start_date: Optional[str] = None,
                   end_date: Optional[str] = None, sources: List[str] = None,
                   exclude_keywords: List[str] = None, require_keywords: List[str] = None) -> List[Paper]:
        """
        在所有选定的搜索引擎上搜索
        
        Args:
            keywords: 搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            sources: 要搜索的来源列表，默认全部
            exclude_keywords: 排除关键词列表
            require_keywords: 必需关键词列表
            
        Returns:
            所有搜索结果的合并列表
        """
        if sources is None:
            sources = list(self.engines.keys())
        
        # 从Config获取过滤设置
        if exclude_keywords is None:
            exclude_keywords = Config.EXCLUDE_KEYWORDS
        if require_keywords is None:
            require_keywords = Config.REQUIRE_KEYWORDS
        
        enable_filter = Config.ENABLE_SMART_FILTER and (exclude_keywords or require_keywords)
        
        if enable_filter:
            print(f"\n🎯 智能过滤已启用:")
            if exclude_keywords:
                print(f"   排除关键词: {', '.join(exclude_keywords)}")
            if require_keywords:
                print(f"   必需关键词: {', '.join(require_keywords)}")
            print()
            
        all_papers = []
        
        for source in sources:
            if source in self.engines:
                print(f"正在搜索 {source}...")
                papers = self.engines[source].search(keywords, start_date, end_date)
                
                # 应用智能过滤
                if enable_filter:
                    original_count = len(papers)
                    papers = [p for p in papers if self._filter_paper(p, exclude_keywords, require_keywords)]
                    filtered_count = original_count - len(papers)
                    if filtered_count > 0:
                        print(f"  ✅ 过滤掉 {filtered_count} 篇不相关论文")
                
                all_papers.extend(papers)
                print(f"从 {source} 找到 {len(papers)} 篇论文")
                
        return all_papers


# 创建全局搜索管理器实例
search_manager = SearchManager()
