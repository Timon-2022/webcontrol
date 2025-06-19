# AI网站配置
AI_WEBSITES = [
    {
        "name": "OpenAI",
        "url": "https://openai.com",
        "search_url": "https://openai.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Anthropic",
        "url": "https://anthropic.com",
        "search_url": "https://anthropic.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Google AI",
        "url": "https://ai.google",
        "search_url": "https://ai.google/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Microsoft AI",
        "url": "https://www.microsoft.com/ai",
        "search_url": "https://www.microsoft.com/ai/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Meta AI",
        "url": "https://ai.meta.com",
        "search_url": "https://ai.meta.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "DeepMind",
        "url": "https://deepmind.com",
        "search_url": "https://deepmind.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Hugging Face",
        "url": "https://huggingface.co",
        "search_url": "https://huggingface.co/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Stability AI",
        "url": "https://stability.ai",
        "search_url": "https://stability.ai/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Cohere",
        "url": "https://cohere.ai",
        "search_url": "https://cohere.ai/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Claude",
        "url": "https://claude.ai",
        "search_url": "https://claude.ai/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Perplexity",
        "url": "https://perplexity.ai",
        "search_url": "https://perplexity.ai/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "You.com",
        "url": "https://you.com",
        "search_url": "https://you.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Bard",
        "url": "https://bard.google.com",
        "search_url": "https://bard.google.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "ChatGPT",
        "url": "https://chat.openai.com",
        "search_url": "https://chat.openai.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Bing Chat",
        "url": "https://www.bing.com/chat",
        "search_url": "https://www.bing.com/chat/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Midjourney",
        "url": "https://www.midjourney.com",
        "search_url": "https://www.midjourney.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "DALL-E",
        "url": "https://openai.com/dall-e-2",
        "search_url": "https://openai.com/dall-e-2/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Runway",
        "url": "https://runwayml.com",
        "search_url": "https://runwayml.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "ElevenLabs",
        "url": "https://elevenlabs.io",
        "search_url": "https://elevenlabs.io/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    },
    {
        "name": "Replicate",
        "url": "https://replicate.com",
        "search_url": "https://replicate.com/search?q={query}",
        "search_selector": "input[name='q'], input[type='search'], .search-input",
        "results_selector": ".search-result, .result-item, article, .content-item"
    }
]

# 搜索配置
SEARCH_CONFIG = {
    "max_results_per_site": 10,  # 每个网站最多获取的结果数
    "wait_time": 3,  # 页面加载等待时间（秒）
    "timeout": 30,  # 超时时间（秒）
    "headless": False,  # 是否无头模式
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 数据存储配置
DATA_CONFIG = {
    "output_dir": "data",
    "results_file": "search_results.json",
    "analysis_file": "analysis_results.json",
    "logs_file": "scraping_logs.txt"
} 