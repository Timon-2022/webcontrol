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
        try:
            self.playwright = await async_playwright().start()
            
            # 使用更简单的启动参数
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # 改为无头模式，避免GUI问题
                args=browser_args,
                timeout=60000,
            )
            
            # 创建页面上下文
            context = await self.browser.new_context(
                user_agent=SEARCH_CONFIG['user_agent'],
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True,
            )
            
            self.page = await context.new_page()
            
            # 设置页面超时
            self.page.set_default_timeout(SEARCH_CONFIG['timeout'] * 1000)
            
            logger.info("浏览器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            return False
        
    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")
            
    async def search_website(self, website: Dict, query: str) -> List[Dict]:
        """在指定网站搜索关键词"""
        results = []
        try:
            logger.info(f"正在搜索 {website['name']} 网站，关键词: {query}")
            
            # 确保page已初始化
            if not self.page:
                logger.error("页面未初始化")
                return results
            
            # 访问网站主页
            await self.page.goto(website['url'], timeout=SEARCH_CONFIG['timeout'] * 1000)
            await self.page.wait_for_timeout(SEARCH_CONFIG['wait_time'] * 1000)
            
            # 检查是否为聊天形式的网站
            if website.get('is_chat', False):
                results = await self._chat_search(website, query)
            else:
                results = await self._normal_search(website, query)
            
            logger.info(f"从 {website['name']} 获取到 {len(results)} 个结果")
            
        except Exception as e:
            logger.error(f"搜索 {website['name']} 时出错: {e}")
            
        return results
    
    async def _chat_search(self, website: Dict, query: str) -> List[Dict]:
        """聊天形式的搜索"""
        results = []
        try:
            # 等待聊天输入框出现
            chat_input = None
            for selector in website['search_selector'].split(', '):
                try:
                    chat_input = await self.page.wait_for_selector(selector.strip(), timeout=10000)
                    if chat_input:
                        break
                except:
                    continue
            
            if not chat_input:
                logger.warning(f"在 {website['name']} 未找到聊天输入框")
                return results
            
            # 构造聊天提示
            chat_prompt = website.get('chat_prompt', '请回答关于以下关键词的问题：{query}').format(query=query)
            
            # 输入聊天内容
            await chat_input.fill(chat_prompt)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息（通常是按Enter键）
            await chat_input.press('Enter')
            
            # 等待回复
            logger.info(f"等待 {website['name']} 回复...")
            await self.page.wait_for_timeout(SEARCH_CONFIG['chat_wait_time'] * 1000)
            
            # 尝试多次等待回复
            for attempt in range(SEARCH_CONFIG['max_chat_attempts']):
                try:
                    # 查找回复内容
                    response_selectors = website['results_selector'].split(', ')
                    for selector in response_selectors:
                        try:
                            response_elements = await self.page.query_selector_all(selector.strip())
                            if response_elements:
                                for i, element in enumerate(response_elements):
                                    try:
                                        # 获取回复文本
                                        response_text = await element.inner_text()
                                        if response_text and len(response_text.strip()) > 10:
                                            result = {
                                                'website': website['name'],
                                                'website_url': website['url'],
                                                'query': query,
                                                'title': f"{website['name']} 回复",
                                                'link': website['url'],
                                                'content': response_text.strip(),
                                                'image': "",
                                                'timestamp': datetime.now().isoformat(),
                                                'rank': i + 1,
                                                'type': 'chat_response'
                                            }
                                            results.append(result)
                                            logger.info(f"获取到 {website['name']} 回复: {response_text[:50]}...")
                                break
                        except Exception as e:
                            logger.debug(f"选择器 {selector} 失败: {e}")
                            continue
                    
                    if results:
                        break
                    else:
                        # 如果没找到回复，再等一下
                        await self.page.wait_for_timeout(3000)
                        
                except Exception as e:
                    logger.debug(f"第 {attempt + 1} 次尝试获取回复失败: {e}")
                    await self.page.wait_for_timeout(2000)
            
            if not results:
                logger.warning(f"未能从 {website['name']} 获取到回复")
                
        except Exception as e:
            logger.error(f"聊天搜索 {website['name']} 时出错: {e}")
            
        return results
    
    async def _normal_search(self, website: Dict, query: str) -> List[Dict]:
        """普通搜索形式"""
        results = []
        try:
            # 尝试查找搜索框
            search_input = None
            for selector in website['search_selector'].split(', '):
                try:
                    search_input = await self.page.wait_for_selector(selector.strip(), timeout=5000)
                    if search_input:
                        break
                except:
                    continue
                    
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
                    if link_elem and hasattr(link_elem, 'get'):
                        href = link_elem.get('href')
                        if href and isinstance(href, str):
                            link = href
                            if link.startswith('/'):
                                link = website['url'].rstrip('/') + link
                    
                    # 提取内容摘要
                    content = element.get_text(strip=True)
                    if len(content) > 500:
                        content = content[:500] + "..."
                    
                    # 提取图片
                    image = ""
                    img_elem = element.find('img')
                    if img_elem and hasattr(img_elem, 'get'):
                        src = img_elem.get('src')
                        if src and isinstance(src, str):
                            image = src
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
                        'rank': i + 1,
                        'type': 'search_result'
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"提取搜索结果时出错: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"普通搜索 {website['name']} 时出错: {e}")
            
        return results
    
    async def scrape_all_websites(self, query: str) -> List[Dict]:
        """在所有配置的网站上搜索关键词"""
        all_results = []
        
        try:
            # 初始化浏览器
            if not await self.init_browser():
                logger.error("浏览器初始化失败，无法继续搜索")
                return all_results
            
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
            logger.error(f"搜索过程中出错: {e}")
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