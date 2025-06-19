# AI 网站自动化搜索与分析工具

一个基于 Python 和 Playwright 的自动化工具，支持访问多个 AI 网站，搜索关键词并保存联网搜索结果，然后用 AI 分析这些网页中关键词的频度、相关性、情绪和权威性。

## 🚀 主要功能

### 1. 多网站搜索
- **DeepSeek** - 支持联网搜索
- **ChatGPT** - 支持聊天搜索
- **其他 AI 网站** - 可扩展支持更多网站

### 2. 登录态复用
- 支持手动登录并保存登录状态
- 自动复用登录状态，无需重复登录
- 支持 DeepSeek 和 ChatGPT 的登录态管理

### 3. 智能内容获取
- 自动识别聊天输入框和回复内容
- 支持多种页面结构的选择器
- 智能等待和重试机制

### 4. 数据分析
- 关键词频度分析
- 内容相关性评估
- 情绪分析
- 权威性评估

## 📁 项目结构

```
script/
├── main.py                 # 主程序入口
├── web_scraper.py          # 网页抓取核心模块
├── ai_analyzer.py          # AI 分析模块
├── login_manager.py        # 登录态管理工具
├── chat_with_login.py      # 支持登录态的聊天搜索
├── deepseek_web_search.py  # DeepSeek 联网搜索
├── config.py               # 配置文件
├── requirements.txt        # 依赖包列表
├── setup.py               # 安装脚本
├── LOGIN_GUIDE.md         # 登录态复用使用指南
├── data/                  # 数据存储目录
└── test_*.py              # 各种测试脚本
```

## 🛠️ 安装与配置

### 1. 环境要求
- Python 3.8+
- macOS/Linux/Windows

### 2. 安装依赖
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
python -m playwright install
```

### 3. 快速安装
```bash
python setup.py
```

## 📖 使用指南

### 1. 登录态管理

#### 首次使用 - 手动登录
```bash
python3 login_manager.py
```
选择选项 1 进行手动登录，程序会：
- 打开浏览器窗口
- 访问目标网站
- 等待你手动完成登录
- 自动保存登录状态

#### 验证登录状态
```bash
python3 login_manager.py
```
选择选项 3 验证登录状态是否有效。

### 2. 聊天搜索

#### DeepSeek 联网搜索
```bash
python3 deepseek_web_search.py
```
输入关键词，程序会：
- 自动使用保存的登录状态
- 访问 DeepSeek 聊天页面
- 发送搜索请求
- 获取 AI 回复
- 保存结果到 JSON 文件

#### 通用聊天搜索
```bash
python3 chat_with_login.py
```
支持选择不同的 AI 平台进行聊天搜索。

### 3. 网页搜索与分析
```bash
python3 main.py
```
执行完整的搜索和分析流程。

## 🔧 配置说明

### 网站配置
在 `config.py` 中配置要搜索的网站：

```python
WEBSITES = [
    {
        'name': 'DeepSeek',
        'url': 'https://chat.deepseek.com',
        'type': 'chat'
    },
    {
        'name': 'ChatGPT', 
        'url': 'https://chat.openai.com',
        'type': 'chat'
    }
]
```

### 搜索关键词
在 `config.py` 中配置搜索关键词：

```python
SEARCH_KEYWORDS = [
    '人工智能',
    '机器学习',
    '深度学习'
]
```

## 📊 数据格式

搜索结果保存为 JSON 格式：

```json
{
    "website": "DeepSeek",
    "website_url": "https://chat.deepseek.com",
    "query": "人工智能",
    "title": "DeepSeek 回复",
    "content": "AI 回复内容...",
    "timestamp": "2025-06-19T17:30:00",
    "success": true
}
```

## 🧪 测试

### 浏览器测试
```bash
python3 test_browser_simple.py
```

### 登录态测试
```bash
python3 login_manager.py
```

### 聊天功能测试
```bash
python3 chat_with_login.py
```

## 🔒 安全注意事项

1. **登录状态文件** - `login_state.json` 包含敏感信息，已添加到 `.gitignore`
2. **个人数据** - 不要将包含个人信息的文件提交到版本控制
3. **API 密钥** - 如有使用 API，请妥善保管密钥

## 🐛 故障排除

### 浏览器启动失败
```bash
# 重新安装 Playwright 浏览器
python -m playwright install
```

### 登录状态失效
```bash
# 重新登录
python3 login_manager.py
```

### 页面元素识别失败
- 网站可能更新了页面结构
- 运行调试脚本分析页面结构
- 更新选择器配置

## 📝 更新日志

### v2.0.0 (2025-06-19)
- ✨ 添加登录态复用功能
- ✨ 支持 DeepSeek 联网搜索
- ✨ 支持 ChatGPT 聊天搜索
- 🔧 优化浏览器启动参数
- 📚 添加详细使用指南

### v1.0.0 (2025-06-18)
- 🎉 初始版本发布
- ✨ 基础网页抓取功能
- ✨ AI 内容分析功能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请提交 GitHub Issue。 