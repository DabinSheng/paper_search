import os
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # Qwen API配置
    QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
    QWEN_API_URL = os.getenv('QWEN_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    QWEN_MODEL = 'qwen-plus'  # 可选: qwen-turbo, qwen-plus, qwen-max
    
    # 翻译配置
    AUTO_TRANSLATE = False  # 是否自动翻译标题和摘要
    
    # 搜索配置
    MAX_RESULTS = 100  # 每次搜索最大结果数
    
    # 智能过滤配置
    ENABLE_SMART_FILTER = True  # 是否启用智能过滤
    EXCLUDE_KEYWORDS = []  # 排除关键词列表（标题或摘要中包含这些词的论文会被过滤）
    REQUIRE_KEYWORDS = []  # 必需关键词列表（至少包含一个的论文才会保留）
    
    # 下载配置
    date_suffix = datetime.now().strftime('%Y%m%d')
    DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser('~'), 'Downloads', f'papers_{date_suffix}')
    
    @classmethod
    def validate(cls):
        """验证必要的配置是否存在"""
        if not cls.QWEN_API_KEY:
            raise ValueError("QWEN_API_KEY 未设置，请在.env文件中配置")
        return True
