# 📚 学术文献检索Agent

基于Qwen API的智能学术文献检索和下载工具，支持从ArXiv、OpenReview、Google Scholar等平台搜索论文，提供中英文自动翻译功能，支持防重复下载和历史记录管理。

## ✨ 主要功能

- 🔍 **多平台搜索**: 支持ArXiv、OpenReview、Google Scholar
- 📅 **智能日期筛选**: 默认搜索近3天论文，支持自定义日期范围
- 🌐 **自动翻译**: 使用Qwen API自动翻译标题和摘要，中英双语对照
- 📥 **批量下载**: 勾选感兴趣的论文批量下载PDF
- ✅ **防重复下载**: 自动记录下载历史，标注已下载论文
- 🎨 **友好界面**: 基于Streamlit的现代化Web界面，支持前端控制设置
- 📊 **下载历史**: 累计下载统计，可查看和管理历史记录

---

## 🚀 快速开始

### 一分钟启动

```bash
# 1. 进入项目目录
cd /Users/shengdabin/Desktop/machine_learning/search

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥（编辑.env文件）
cp .env.example .env
# 将 QWEN_API_KEY 替换为你的实际密钥

# 4. 启动应用
./start.sh
# 或者: streamlit run app.py
```

浏览器自动打开: http://localhost:8501

---

## 📖 详细使用指南

### 1. 环境配置

#### 系统要求
- Python 3.8+
- 稳定的网络连接
- Qwen API密钥

#### 获取Qwen API密钥

1. 访问 [阿里云百炼平台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 进入"API-KEY管理"
4. 创建新密钥
5. 复制并填入 `.env` 文件

#### 配置文件

创建 `.env` 文件:
```bash
cp .env.example .env
```

编辑 `.env` 文件内容:
```env
QWEN_API_KEY=sk-你的实际密钥
QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 2. 搜索功能

#### 搜索参数设置

**关键词输入**:
- 支持单个或多个关键词
- 建议使用英文术语
- 示例: `deep learning`, `transformer attention mechanism`

**日期范围**:
- 默认: 最近3天（可修改）
- 自定义: 开始日期和结束日期
- 建议: 不要设置过大范围以提高搜索速度

**数据源选择**:
- **ArXiv**: 最推荐，覆盖计算机、数学、物理等领域
- **OpenReview**: 主要是机器学习会议论文，质量较高
- **Google Scholar**: 覆盖面广但可能不稳定

**搜索设置**:
- 最大结果数: 前端UI可调整（默认100）
- 自动翻译: 前端UI可开关（默认开启）

#### 搜索技巧

**精确搜索**:
```
"attention mechanism"  # 使用引号精确匹配
```

**组合关键词**:
```
deep learning computer vision  # 空格分隔
```

**缩小范围**:
```
transformer natural language processing BERT  # 更具体的术语
```

### 3. 浏览和翻译

#### 自动翻译功能

搜索完成后，系统会自动：
1. 显示翻译进度条
2. 批量翻译所有论文的标题和摘要
3. 缓存翻译结果

**显示效果**:
- 标题: 英文下方显示中文（淡蓝色背景）
- 摘要: 展开后同时显示英文和中文

**关闭自动翻译**: 在前端UI取消勾选"自动翻译"

#### 论文信息展示

每篇论文显示:
- ✅ 标题（中英双语）
- ✅ 作者列表
- ✅ 发表日期
- ✅ 来源平台
- ✅ 论文链接和PDF链接
- ✅ 摘要（中英双语）
- ✅ 下载状态（已下载标记）

### 4. 下载管理

#### 防重复下载

**工作原理**:
- 每次下载成功后自动记录到历史文件
- 历史文件: `paper_search_history.json`（项目根目录）
- 已下载论文自动标记为"✅ 已下载"
- 勾选框自动禁用，防止重复下载

**显示标记**:
- 已下载论文显示绿色提示框
- 标注下载日期
- 勾选框禁用且灰色显示

#### 批量下载

**操作步骤**:
1. 浏览搜索结果，查看中文翻译
2. 勾选感兴趣的论文（已下载的无法勾选）
3. 使用"全选"/"取消全选"快速操作
4. 点击"下载选中论文"按钮
5. 等待下载完成，查看统计信息

**下载统计**:
- ✅ 成功下载 X 篇
- ℹ️ 跳过 Y 篇（已下载）
- ⚠️ Z 篇下载失败
- 📁 保存位置
- 📊 累计下载 N 篇

#### 下载路径设置

**默认路径**: `~/Downloads/papers_YYYYMMDD`
- 每天自动创建新文件夹
- 按日期组织下载的论文

**自定义路径**: 在侧边栏"下载设置"中修改

**推荐结构**:
```
Papers/
├── DeepLearning/
│   ├── Vision/
│   ├── NLP/
│   └── Reinforcement/
├── MachineLearning/
└── DataScience/
```

### 5. 历史记录管理

#### 查看历史

侧边栏显示:
- 累计下载数量
- 清空历史记录按钮

#### 历史文件

**位置**: `paper_search_history.json`（项目根目录）

**格式**:
```json
{
  "deep learning for computer vision": {
    "title": "Deep Learning for Computer Vision",
    "file_path": "/Users/xxx/Downloads/papers_20251126/paper.pdf",
    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
    "download_date": "2025-11-26 14:30:25",
    "date_only": "2025-11-26"
  }
}
```

#### 清空历史

- 点击侧边栏"🗑️ 清空历史记录"
- 清空后所有论文可重新下载
- 不会删除已下载的文件

#### 备份历史

```bash
# 备份（在项目根目录执行）
cp paper_search_history.json ~/paper_history_backup.json

# 恢复
cp ~/paper_history_backup.json paper_search_history.json
```

---

## 📁 项目结构

```
search/
├── app.py                  # Streamlit主应用
├── config.py              # 配置管理
├── qwen_client.py         # Qwen API客户端
├── search_engines.py      # 搜索引擎实现
├── download_manager.py    # 下载管理器
├── download_history.py    # 下载历史管理
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量示例
├── .env                  # 环境变量（需自行创建）
├── .gitignore           # Git忽略文件
├── start.sh             # 启动脚本
└── README.md            # 项目文档
```

### 核心模块说明

**app.py** - 主应用
- Streamlit Web界面
- 用户交互逻辑
- 功能集成

**config.py** - 配置管理
- 环境变量加载
- 配置参数定义
- 主要配置项:
  - `QWEN_API_KEY`: Qwen API密钥
  - `QWEN_API_URL`: API地址（OpenAI兼容模式）
  - `QWEN_MODEL`: 使用的模型（qwen-plus）
  - `MAX_RESULTS`: 搜索最大结果数（默认100）
  - `AUTO_TRANSLATE`: 自动翻译开关（默认True）
  - `DEFAULT_DOWNLOAD_PATH`: 默认下载路径（带日期后缀）

**qwen_client.py** - 翻译客户端
- Qwen API调用封装（OpenAI兼容格式）
- 翻译功能实现
- 错误处理

**search_engines.py** - 搜索引擎
- 多平台搜索实现
- 统一论文数据格式
- 支持平台: ArXiv、OpenReview、Google Scholar

**download_manager.py** - 下载管理
- PDF文件下载
- 批量下载管理
- 集成历史记录检查
- 防重复下载

**download_history.py** - 历史管理
- 下载记录持久化
- 检查是否已下载
- 累计统计

---

## 🔧 配置和优化

### 模型选择

编辑 `config.py`:
```python
QWEN_MODEL = 'qwen-turbo'  # 快速，低成本
# QWEN_MODEL = 'qwen-plus'   # 平衡（推荐）
# QWEN_MODEL = 'qwen-max'    # 高质量，高成本
```

### 搜索配置

前端UI直接调整:
- 最大结果数滑块: 10-200
- 自动翻译开关

或编辑 `config.py`:
```python
MAX_RESULTS = 100  # 每次搜索最大结果数
AUTO_TRANSLATE = True  # 是否自动翻译
```

### 性能优化

**搜索优化**:
- 减少数据源数量（只选ArXiv）
- 缩小日期范围
- 使用更具体的关键词

**翻译优化**:
- 翻译结果自动缓存
- 关闭自动翻译（手动翻译需要的内容）
- 调整最大结果数

**下载优化**:
- 批量下载不要选择太多（建议20篇以内）
- 定期清理下载目录

---

## 🛠️ 技术栈

### 前端
- **Streamlit 1.28+**: Web界面框架
- **HTML/CSS**: 自定义样式

### 后端
- **Python 3.8+**: 主要编程语言
- **Requests**: HTTP客户端
- **BeautifulSoup4**: HTML解析
- **ArXiv 2.1.0**: ArXiv API客户端

### API服务
- **Qwen API**: 阿里云百炼大模型（OpenAI兼容模式）
- **ArXiv API**: 预印本论文检索
- **OpenReview V2 API**: 会议论文检索

---

## 🎯 智能过滤系统

### 功能概述

智能过滤系统可以帮助您过滤掉不相关的论文，提高搜索结果的准确性。特别适合处理宽泛关键词搜索时出现的大量无关结果。

### 使用场景

#### 场景1: LLM Memory研究

**问题**: 搜索"memory"时会返回大量硬件、化学相关的无关论文

**解决方案**:
- **排除关键词**: `hardware`, `circuit`, `chip`, `semiconductor`, `memory cell`, `storage device`, `RAM`, `DRAM`
- **必需关键词**: `language model`, `LLM`, `neural network`, `deep learning`, `transformer`

#### 场景2: 计算机视觉中的Attention机制

**问题**: 搜索"attention"时会返回心理学、医学相关论文

**解决方案**:
- **排除关键词**: `psychology`, `medical`, `clinical`, `patient`, `disorder`, `cognitive therapy`
- **必需关键词**: `computer vision`, `image`, `visual`, `CNN`, `neural network`

### 配置方式

**通过UI配置（推荐）**:
1. 打开侧边栏"⚙️ 高级设置"
2. 展开"🎯 智能过滤"
3. 启用"启用智能过滤"开关
4. 输入排除关键词和必需关键词（每行一个）

**效果示例**:
- 搜索 "memory" 无过滤: 100篇（30篇相关）→ 准确率30%
- 启用智能过滤: 35篇（30篇相关）→ 准确率86%

### 使用技巧

1. **排除关键词**: 使用具体术语，包含复数形式和常见搭配
2. **必需关键词**: 不要过于严格，建议2-5个，使用同义词和缩写
3. **平衡调整**: 优先使用排除关键词，逐步根据结果调整

---

## 📜 搜索历史功能

### 自动保存

系统会自动保存您的搜索历史，包括：
- 搜索关键词
- 日期范围
- 数据源选择
- 排除关键词
- 必需关键词

### 快速恢复

在搜索界面：
1. 点击"最近搜索"下拉框
2. 选择历史记录
3. 自动填充所有搜索参数
4. 一键重新搜索

### 历史管理

- **查看历史**: 展开"📜 搜索历史"查看最近10次搜索
- **清空历史**: 点击"🗑️ 清空搜索历史"
- **历史文件**: `search_history.json`（项目根目录）

---

## 🐛 常见问题

### Q1: 搜索没有结果？

**检查**:
- 关键词是否正确（建议使用英文）
- 日期范围是否过窄（默认3天）
- 网络连接是否正常
- 选择的数据源是否合适

**解决**:
- 使用更宽泛的关键词
- 扩大日期范围
- 尝试多个数据源

### Q2: 翻译功能不可用？

**检查**:
- `.env` 文件中的 `QWEN_API_KEY` 是否正确
- API密钥是否有效且有剩余配额
- 网络能否访问阿里云服务
- API URL 是否为OpenAI兼容模式地址

**测试API连接**:
```bash
python3 -c "from qwen_client import QwenClient; client = QwenClient(); print(client.translate_to_chinese('test'))"
```

### Q3: PDF下载失败？

**可能原因**:
- 论文没有公开PDF链接
- 需要订阅或权限才能下载
- 网络连接问题
- 文件名包含特殊字符

**解决方法**:
- 访问论文原页面手动下载
- 通过学校图书馆访问
- 联系作者获取预印本

### Q4: OpenReview搜索不到结果？

**原因**: 
- OpenReview V2 API限制
- 关键词不匹配
- 日期范围问题

**解决**: 
- 使用更通用的关键词
- 扩大日期范围
- 优先使用ArXiv

### Q5: 下载历史如何管理？

**查看**: 侧边栏显示累计下载数量

**清空**: 点击"🗑️ 清空历史记录"

**备份**: 
```bash
# 在项目根目录执行
cp paper_search_history.json ~/backup.json
```

### Q6: 如何关闭自动翻译？

**方法1**: 前端UI取消勾选"自动翻译"

**方法2**: 编辑 `config.py`
```python
AUTO_TRANSLATE = False
```

---

## ⚠️ 注意事项

### API配额管理
- Qwen API可能有调用次数限制
- 自动翻译会消耗更多配额
- 每篇论文标题+摘要 = 2次API调用
- 建议控制搜索结果数量或只翻译标题

### 网络要求
- 需要稳定的网络连接
- 能访问国际学术网站
- 阿里云服务可达

### 合规使用
- 遵守各平台的使用条款
- 尊重论文版权
- 仅用于学术研究

### 已知限制

1. **Google Scholar**: 爬虫方式不太稳定，可能被反爬虫限制
2. **PDF下载**: 部分论文可能无公开PDF或需要订阅
3. **翻译质量**: 依赖Qwen API，专业术语可能需要人工校对

---

## 📊 使用示例

### 示例1: 搜索深度学习论文

```
关键词: deep learning computer vision
开始日期: 2024-01-01
结束日期: 2025-01-26
数据源: ✅ ArXiv ✅ OpenReview
最大结果数: 50
自动翻译: ✅
```

### 示例2: 搜索Transformer论文

```
关键词: transformer attention mechanism
日期: 最近3天（默认）
数据源: ✅ ArXiv
最大结果数: 100
自动翻译: ✅
```

### 示例3: 批量下载流程

1. 搜索 "machine learning"
2. 系统自动翻译所有结果
3. 浏览中文标题和摘要
4. 勾选感兴趣的论文（5-10篇）
5. 点击"下载选中论文"
6. 查看统计: 成功X篇，跳过Y篇（已下载）
7. 在 `~/Downloads/papers_20251126/` 查看文件

---

## 🚀 进阶使用

### 自定义搜索引擎

在 `search_engines.py` 中添加新的搜索源:

```python
class NewSearchEngine(SearchEngine):
    def search(self, keywords, start_date, end_date):
        # 实现搜索逻辑
        pass
```

### 修改界面样式

编辑 `app.py` 中的CSS:

```python
st.markdown("""
<style>
    /* 你的自定义样式 */
</style>
""", unsafe_allow_html=True)
```

### 扩展翻译功能

在 `qwen_client.py` 中添加新方法:

```python
def custom_translate(self, text, style='academic'):
    # 自定义翻译逻辑
    pass
```

---

## 📝 部署检查清单

### 必需步骤

- [ ] 已安装 Python 3.8+
- [ ] 执行 `pip install -r requirements.txt`
- [ ] 获取 Qwen API 密钥
- [ ] 编辑 `.env` 文件，填入正确的密钥
- [ ] `start.sh` 具有执行权限

### 测试验证

```bash
# 1. 配置验证
python3 -c "from config import Config; Config.validate(); print('✅ 配置验证成功')"

# 2. 依赖检查
python3 -c "import streamlit, arxiv, requests; print('✅ 依赖检查成功')"

# 3. 启动应用
streamlit run app.py
```

### 功能测试

- [ ] 搜索功能正常（测试关键词: "deep learning"）
- [ ] 自动翻译正常（显示中英双语）
- [ ] 下载功能正常（测试下载1篇论文）
- [ ] 历史记录正常（再次搜索显示已下载标记）

---

## 🎯 开发计划

- [ ] 添加更多搜索源（IEEE、Springer、PubMed）
- [ ] 支持PDF内容提取和分析
- [ ] 添加论文笔记和标签功能
- [ ] 支持导出搜索结果为CSV/Excel/BibTeX
- [ ] 论文推荐系统
- [ ] 多语言界面支持
- [ ] 移动端适配

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 📧 联系与支持

- **问题反馈**: 通过 GitHub Issues 联系
- **功能建议**: 欢迎提交 Issue 讨论
- **技术支持**: 查看文档和常见问题

---

## 🙏 致谢

感谢以下开源项目:
- [Streamlit](https://streamlit.io/) - Web界面框架
- [ArXiv Python Client](https://pypi.org/project/arxiv/) - ArXiv API客户端
- [Requests](https://requests.readthedocs.io/) - HTTP库
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML解析
- [Python-dotenv](https://pypi.org/project/python-dotenv/) - 环境变量管理



**Powered by Qwen API** | Made with ❤️ using Streamlit



**开始使用**: `./start.sh` 或 `streamlit run app.py`
