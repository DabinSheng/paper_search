import os
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class DownloadHistory:
    """下载历史管理"""
    
    def __init__(self, history_file: str = None):
        """
        初始化下载历史管理器
        
        Args:
            history_file: 历史记录文件路径
        """
        if history_file is None:
            # 默认保存在项目根目录
            project_root = os.path.dirname(os.path.abspath(__file__))
            history_file = os.path.join(
                project_root, 
                'paper_search_history.json'
            )
        
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载历史记录失败: {e}")
                return {}
        return {}
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def is_downloaded(self, paper_title: str, pdf_url: str = None) -> bool:
        """
        检查论文是否已下载
        
        Args:
            paper_title: 论文标题
            pdf_url: PDF链接（可选，用于更精确匹配）
            
        Returns:
            是否已下载
        """
        # 使用标题作为主键
        key = self._normalize_title(paper_title)
        return key in self.history
    
    def get_download_info(self, paper_title: str) -> Optional[Dict]:
        """
        获取下载信息
        
        Args:
            paper_title: 论文标题
            
        Returns:
            下载信息字典，包含日期和路径
        """
        key = self._normalize_title(paper_title)
        return self.history.get(key)
    
    def add_download(self, paper_title: str, file_path: str, pdf_url: str = None):
        """
        添加下载记录
        
        Args:
            paper_title: 论文标题
            file_path: 文件保存路径
            pdf_url: PDF链接
        """
        key = self._normalize_title(paper_title)
        self.history[key] = {
            'title': paper_title,
            'file_path': file_path,
            'pdf_url': pdf_url,
            'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date_only': datetime.now().strftime('%Y-%m-%d')
        }
        self._save_history()
    
    def remove_download(self, paper_title: str):
        """
        移除下载记录
        
        Args:
            paper_title: 论文标题
        """
        key = self._normalize_title(paper_title)
        if key in self.history:
            del self.history[key]
            self._save_history()
    
    def _normalize_title(self, title: str) -> str:
        """
        标准化标题作为键
        
        Args:
            title: 原始标题
            
        Returns:
            标准化后的标题
        """
        # 转小写，去除多余空格
        return ' '.join(title.lower().strip().split())
    
    def clear_history(self):
        """清空历史记录"""
        self.history = {}
        self._save_history()
    
    def get_total_downloads(self) -> int:
        """获取总下载数"""
        return len(self.history)


# 创建全局下载历史实例
download_history = DownloadHistory()
