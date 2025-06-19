import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import requests

from config import AI_WEBSITES, SEARCH_CONFIG, DATA_CONFIG

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_CONFIG['logs_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.results = []
        
    async def init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=SEARCH_CONFIG['headless'],
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = await self.browser.new_page()
        await self.page.set_user_agent(SEARCH_CONFIG['user_agent'])
        
    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
            
    async def search_website(self, website: Dict, query: str) -> List[Dict]:
        """在指定网站搜索关键词"""
        results = []
        try:
            logger.info(f"正在搜索 {website['name']} 网站，关键词: {query}")
            
            # 访问网站主页
            await self.page.goto(website['url'], timeout=SEARCH_CONFIG['timeout'] * 1000)
            await self.page.wait_for_timeout(SEARCH_CONFIG['wait_time'] * 1000)
            
            # 尝试查找搜索框
            search_input = None
            try:
                search_input = await self.page.wait_for_selector(
                    website['search_selector'], 
                    timeout=5000
                )
            except:
                logger.warning(f"在 {website['name']} 未找到搜索框，尝试直接访问搜索URL")
                
            if search_input:
                # 在搜索框中输入关键词
                await search_input.fill(query)
                await search_input.press('Enter')
                await self.page.wait_for_timeout(SEARCH_CONFIG['wait_time'] * 1000)
            else:
                # 直接访问搜索URL
                search_url = website['search_url'].format(query=query)
                await self.page.goto(search_url, timeout=SEARCH_CONFIG['timeout'] * 1000)
                await self.page.wait_for_timeout(SEARCH_CONFIG['wait_time'] * 1000)
            
            # 获取页面内容
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 提取搜索结果
            result_elements = soup.select(website['results_selector'])
            
            for i, element in enumerate(result_elements[:SEARCH_CONFIG['max_results_per_site']]):
                try:
                    # 提取标题
                    title = ""
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', '.title'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # 提取链接
                    link = ""
                    link_elem = element.find('a')
                    if link_elem and link_elem.get('href'):
                        link = link_elem.get('href')
                        if link.startswith('/'):
                            link = website['url'].rstrip('/') + link
                    
                    # 提取内容摘要
                    content = element.get_text(strip=True)
                    if len(content) > 500:
                        content = content[:500] + "..."
                    
                    # 提取图片
                    image = ""
                    img_elem = element.find('img')
                    if img_elem and img_elem.get('src'):
                        image = img_elem.get('src')
                        if image.startswith('/'):
                            image = website['url'].rstrip('/') + image
                    
                    result = {
                        'website': website['name'],
                        'website_url': website['url'],
                        'query': query,
                        'title': title,
                        'link': link,
                        'content': content,
                        'image': image,
                        'timestamp': datetime.now().isoformat(),
                        'rank': i + 1
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"提取搜索结果时出错: {e}")
                    continue
            
            logger.info(f"从 {website['name']} 获取到 {len(results)} 个结果")
            
        except Exception as e:
            logger.error(f"搜索 {website['name']} 时出错: {e}")
            
        return results
    
    async def scrape_all_websites(self, query: str) -> List[Dict]:
        """在所有配置的网站上搜索关键词"""
        all_results = []
        
        try:
            await self.init_browser()
            
            for website in AI_WEBSITES:
                try:
                    results = await self.search_website(website, query)
                    all_results.extend(results)
                    
                    # 添加延迟避免被反爬
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"处理网站 {website['name']} 时出错: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
        finally:
            await self.close_browser()
            
        return all_results
    
    def save_results(self, results: List[Dict], query: str):
        """保存搜索结果到本地文件"""
        # 创建输出目录
        os.makedirs(DATA_CONFIG['output_dir'], exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_CONFIG['output_dir']}/search_results_{query}_{timestamp}.json"
        
        # 保存结果
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'websites_searched': len(set(r['website'] for r in results)),
                'results': results
            }, f, ensure_ascii=False, indent=2)
            
        logger.info(f"搜索结果已保存到: {filename}")
        return filename

async def main():
    """主函数"""
    scraper = WebScraper()
    
    # 获取用户输入的关键词
    query = input("请输入要搜索的关键词: ").strip()
    if not query:
        print("关键词不能为空！")
        return
    
    print(f"开始搜索关键词: {query}")
    print("正在访问20个AI网站...")
    
    # 执行搜索
    results = await scraper.scrape_all_websites(query)
    
    # 保存结果
    if results:
        filename = scraper.save_results(results, query)
        print(f"搜索完成！共获取到 {len(results)} 个结果")
        print(f"结果已保存到: {filename}")
    else:
        print("未获取到任何搜索结果")

if __name__ == "__main__":
    asyncio.run(main()) 