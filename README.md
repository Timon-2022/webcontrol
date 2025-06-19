# AI网站搜索分析工具

这是一个基于 Python + Playwright 的自动化工具，用于访问多个AI网站、搜索关键词并分析结果。

## 功能特点

- 🚀 **自动化浏览器操作**: 使用 Playwright 自动访问20个主流AI网站
- 🔍 **智能搜索**: 自动在各大AI网站搜索指定关键词
- 📊 **数据分析**: 分析关键词频度、相关性、情绪和权威性
- 📈 **详细报告**: 生成包含多种指标的分析报告
- 💾 **本地存储**: 所有结果保存到本地文件，便于后续分析

## 支持的AI网站

1. OpenAI
2. Anthropic
3. Google AI
4. Microsoft AI
5. Meta AI
6. DeepMind
7. Hugging Face
8. Stability AI
9. Cohere
10. Claude
11. Perplexity
12. You.com
13. Bard
14. ChatGPT
15. Bing Chat
16. Midjourney
17. DALL-E
18. Runway
19. ElevenLabs
20. Replicate

## 安装要求

### 系统要求
- Python 3.8+
- macOS/Linux/Windows

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-search-analyzer
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装 Playwright 浏览器**
```bash
playwright install chromium
```

4. **配置环境变量（可选）**
```bash
# 创建 .env 文件
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

## 使用方法

### 快速开始

运行主程序：
```bash
python main.py
```

### 分步执行

1. **仅执行网页搜索**：
```bash
python web_scraper.py
```

2. **仅执行结果分析**：
```bash
python ai_analyzer.py
```

### 程序菜单选项

1. **执行完整流程（搜索 + 分析）**: 自动完成搜索和分析
2. **仅执行网页搜索**: 只进行网站搜索和数据收集
3. **仅执行结果分析**: 分析已有的搜索结果
4. **查看历史结果**: 查看之前保存的结果和报告
5. **退出**: 退出程序

## 输出文件

程序会在 `data/` 目录下生成以下文件：

- `search_results_[关键词]_[时间戳].json`: 原始搜索结果
- `analysis_results_[关键词]_[时间戳].json`: 详细分析结果
- `summary_report_[关键词]_[时间戳].txt`: 摘要报告
- `scraping_logs.txt`: 操作日志

## 分析指标

### 1. 关键词频度分析
- 总出现次数统计
- 各网站关键词出现频度排名
- 标题和内容中的关键词分布

### 2. 相关性分析
- 基于关键词匹配的相关性评分
- 标题权重（60%）+ 内容权重（40%）
- 0-1 分数范围

### 3. 情绪分析
- 使用 TextBlob 进行情绪分析
- 积极/消极/中性情绪分类
- 情绪极性和主观性评分

### 4. 权威性分析
- 基于网站知名度的权威性评分
- 内容长度和质量评估
- 链接和图片完整性检查

### 5. 综合评分
- 相关性（40%）+ 情绪（20%）+ 权威性（40%）
- 自动排序和推荐

## 配置说明

### 修改网站配置
编辑 `config.py` 文件中的 `AI_WEBSITES` 列表来添加或修改目标网站。

### 调整搜索参数
在 `config.py` 中修改 `SEARCH_CONFIG`：
- `max_results_per_site`: 每个网站最多获取的结果数
- `wait_time`: 页面加载等待时间
- `timeout`: 超时时间
- `headless`: 是否无头模式

## 注意事项

1. **反爬虫机制**: 程序已内置延迟和用户代理设置，但仍需遵守网站的robots.txt
2. **网络连接**: 确保网络连接稳定，某些网站可能需要VPN访问
3. **浏览器兼容性**: 建议使用最新版本的Chrome浏览器
4. **数据存储**: 大量数据会占用本地存储空间，定期清理旧文件

## 故障排除

### 常见问题

1. **Playwright 安装失败**
```bash
# 重新安装 Playwright
pip uninstall playwright
pip install playwright
playwright install
```

2. **网站访问失败**
- 检查网络连接
- 确认网站是否可访问
- 尝试使用VPN

3. **分析结果为空**
- 检查关键词是否正确
- 确认搜索结果文件存在
- 查看日志文件了解详细错误

### 日志查看
程序运行时会生成详细的日志文件 `scraping_logs.txt`，遇到问题时请查看此文件。

## 开发说明

### 项目结构
```
ai-search-analyzer/
├── main.py              # 主程序入口
├── web_scraper.py       # 网页抓取模块
├── ai_analyzer.py       # AI分析模块
├── config.py            # 配置文件
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明
└── data/               # 数据输出目录
```

### 扩展功能
- 添加新的AI网站支持
- 自定义分析算法
- 集成更多AI分析服务
- 添加数据可视化功能

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至：[your-email@example.com] 