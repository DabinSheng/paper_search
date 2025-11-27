"""搜索历史管理模块"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class SearchHistory:
    """搜索历史管理类"""
    
    def __init__(self, history_file: str = None):
        """初始化搜索历史管理器"""
        if history_file is None:
            # 保存在项目根目录
            project_root = os.path.dirname(os.path.abspath(__file__))
            history_file = os.path.join(project_root, 'search_history.json')
        
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """从文件加载搜索历史"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载搜索历史失败: {e}")
                return []
        return []
    
    def _save_history(self):
        """保存搜索历史到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存搜索历史失败: {e}")
    
    def add_search(self, keywords: str, exclude_keywords: str = "", 
                   sources: List[str] = None, results_count: int = 0):
        """
        添加搜索记录
        
        Args:
            keywords: 搜索关键词
            exclude_keywords: 排除关键词
            sources: 搜索来源列表
            results_count: 结果数量
        """
        # 检查是否已存在相同的搜索
        for record in self.history:
            if (record.get('keywords') == keywords and 
                record.get('exclude_keywords') == exclude_keywords):
                # 更新已存在的记录
                record['last_search_time'] = datetime.now().isoformat()
                record['search_count'] = record.get('search_count', 1) + 1
                record['sources'] = sources or []
                record['results_count'] = results_count
                self._save_history()
                return
        
        # 添加新记录
        record = {
            'keywords': keywords,
            'exclude_keywords': exclude_keywords,
            'sources': sources or [],
            'results_count': results_count,
            'first_search_time': datetime.now().isoformat(),
            'last_search_time': datetime.now().isoformat(),
            'search_count': 1
        }
        
        # 添加到列表开头
        self.history.insert(0, record)
        
        # 只保留最近100条记录
        self.history = self.history[:100]
        
        self._save_history()
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的搜索记录
        
        Args:
            limit: 返回的记录数量
            
        Returns:
            搜索记录列表
        """
        return self.history[:limit]
    
    def get_last_search(self) -> Optional[Dict]:
        """获取最后一次搜索记录"""
        if self.history:
            return self.history[0]
        return None
    
    def clear_history(self):
        """清空搜索历史"""
        self.history = []
        self._save_history()
    
    def remove_search(self, index: int):
        """删除指定索引的搜索记录"""
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self._save_history()
    
    def get_popular_keywords(self, limit: int = 5) -> List[str]:
        """
        获取最常用的搜索关键词
        
        Args:
            limit: 返回的关键词数量
            
        Returns:
            关键词列表（按使用频率排序）
        """
        keyword_freq = {}
        
        for record in self.history:
            keywords = record.get('keywords', '')
            count = record.get('search_count', 1)
            if keywords:
                keyword_freq[keywords] = keyword_freq.get(keywords, 0) + count
        
        # 按频率排序
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_keywords[:limit]]
    
    def get_popular_excludes(self, limit: int = 5) -> List[str]:
        """
        获取最常用的排除关键词
        
        Args:
            limit: 返回的关键词数量
            
        Returns:
            排除关键词列表（按使用频率排序）
        """
        exclude_freq = {}
        
        for record in self.history:
            excludes = record.get('exclude_keywords', '')
            count = record.get('search_count', 1)
            if excludes:
                exclude_freq[excludes] = exclude_freq.get(excludes, 0) + count
        
        # 按频率排序
        sorted_excludes = sorted(exclude_freq.items(), key=lambda x: x[1], reverse=True)
        return [ex for ex, _ in sorted_excludes[:limit]]


# 创建全局搜索历史管理器实例
search_history = SearchHistory()
