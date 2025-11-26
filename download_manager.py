import os
import requests
from typing import List, Optional
from pathlib import Path
import re
from download_history import download_history


class DownloadManager:
    """PDF下载管理器"""
    
    def __init__(self, download_path: Optional[str] = None):
        """
        初始化下载管理器
        
        Args:
            download_path: 下载路径，如果为None则使用默认路径
        """
        if download_path:
            self.download_path = download_path
        else:
            from config import Config
            self.download_path = Config.DEFAULT_DOWNLOAD_PATH
            
        # 确保下载目录存在
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
        
    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 限制文件名长度
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip()
    
    def download_pdf(self, url: str, title: str, progress_callback=None) -> tuple[bool, str, str]:
        """
        下载单个PDF文件
        
        Args:
            url: PDF的URL
            title: 论文标题，用作文件名
            progress_callback: 进度回调函数
            
        Returns:
            (是否成功, 消息, 文件路径)
        """
        if not url:
            return False, "PDF链接不可用", ""
        
        # 检查是否已下载
        if download_history.is_downloaded(title):
            info = download_history.get_download_info(title)
            return False, f"已下载过 (日期: {info['date_only']})", info.get('file_path', '')
            
        try:
            # 生成文件名
            filename = self.sanitize_filename(title) + ".pdf"
            filepath = os.path.join(self.download_path, filename)
            
            # 如果文件已存在，添加序号
            counter = 1
            original_filepath = filepath
            while os.path.exists(filepath):
                filename = self.sanitize_filename(title) + f"_{counter}.pdf"
                filepath = os.path.join(self.download_path, filename)
                counter += 1
            
            # 下载文件
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            # 检查是否是PDF
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' not in content_type and 'pdf' not in url.lower():
                return False, "链接不是有效的PDF文件", ""
            
            # 写入文件
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 调用进度回调
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress)
            
            # 添加到下载历史
            download_history.add_download(title, filepath, url)
            
            return True, f"成功下载到: {filepath}", filepath
            
        except requests.exceptions.Timeout:
            return False, "下载超时", ""
        except requests.exceptions.RequestException as e:
            return False, f"下载失败: {str(e)}", ""
        except Exception as e:
            return False, f"发生错误: {str(e)}", ""
    
    def download_multiple(self, papers: List[dict], 
                         progress_callback=None) -> dict:
        """
        批量下载多个PDF
        
        Args:
            papers: 论文列表，每个论文包含title和pdf_url
            progress_callback: 进度回调函数
            
        Returns:
            下载结果统计
        """
        results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'total': len(papers)
        }
        
        for idx, paper in enumerate(papers):
            title = paper.get('title', f'paper_{idx}')
            pdf_url = paper.get('pdf_url', '')
            
            if progress_callback:
                progress_callback(idx, len(papers))
            
            success, message, filepath = self.download_pdf(pdf_url, title)
            
            if success:
                results['success'].append({
                    'title': title,
                    'message': message,
                    'filepath': filepath
                })
            elif "已下载过" in message:
                results['skipped'].append({
                    'title': title,
                    'message': message
                })
            else:
                results['failed'].append({
                    'title': title,
                    'message': message
                })
        
        return results
    
    def set_download_path(self, path: str):
        """
        设置下载路径
        
        Args:
            path: 新的下载路径
        """
        self.download_path = path
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
    
    def get_download_path(self) -> str:
        """获取当前下载路径"""
        return self.download_path


# 创建全局下载管理器实例
download_manager = DownloadManager()
