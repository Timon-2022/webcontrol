#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI网站搜索爬虫 - 修复版本
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests

from config import AI_WEBSITES, SEARCH_CONFIG, DATA_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{DATA_CONFIG["output_dir"]}/{DATA_CONFIG["logs_file"]}', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        
    async def init_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # 改为无头模式
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            
            # 创建页面
            context = await self.browser.new_context(
                user_agent=SEARCH_CONFIG['user_agent']
            )
            self.page = await context.new_page()
            
            logger.info("浏览器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False
    
    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")
    
    async def search_website(self, website: Dict, query: str) -> List[Dict]:
        """在指定网站搜索关键词"""
        logger.info(f"开始搜索 {website['name']}: {query}")
        
        # 检查是否是聊天形式
        if website.get('is_chat', False):
            return await self._chat_search(website, query)
        else:
            return await self._normal_search(website, query)
    
    async def _chat_search(self, website: Dict, query: str) -> List[Dict]:
        """聊天形式搜索"""
        results = []
        try:
            # 访问网站
            await self.page.goto(website['url'], timeout=SEARCH_CONFIG['timeout'] * 1000)
            await self.page.wait_for_timeout(3000)
            
            # 查找输入框
            input_element = None
            for selector in website['search_selector'].split(', '):
                try:
                    input_element = await self.page.wait_for_selector(selector.strip(), timeout=5000)
                    if input_element:
                        break
                except:
                    continue
            
            if input_element:
                # 输入聊天内容
                chat_prompt = website.get('chat_prompt', '{query}').format(query=query)
                await input_element.fill(chat_prompt)
                await input_element.press('Enter')
                
                # 等待回复
                await self.page.wait_for_timeout(SEARCH_CONFIG['chat_wait_time'] * 1000)
                
                # 获取回复
                for selector in website['results_selector'].split(', '):
                    try:
                        elements = await self.page.query_selector_all(selector.strip())
                        if elements:
                            for i, element in enumerate(elements[-3:]):  # 获取最后3个回复
                                text = await element.text_content()
                                if text and len(text.strip()) > 20:
                                    result = {
                                        'website': website['name'],
                                        'website_url': website['url'],
                                        'query': query,
                                        'title': f"{website['name']} 回复",
                                        'link': website['url'],
                                        'content': text.strip(),
                                        'image': "",
                                        'timestamp': datetime.now().isoformat(),
                                        'rank': i + 1,
                                        'type': 'chat_response'
                                    }
                                    results.append(result)
                                    logger.info(f"获取到 {website['name']} 回复: {text[:50]}...")
                            break
                    except Exception as e:
                        logger.debug(f"选择器 {selector} 失败: {e}")
                        continue
            
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
                    await self.page.goto(website['url'], timeout=SEARCH_CONFIG['timeout'] * 1000)
                    await self.page.wait_for_timeout(2000)
                    
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
                try:
                    search_url = website['search_url'].format(query=query)
                    await self.page.goto(search_url, timeout=SEARCH_CONFIG['timeout'] * 1000)
                    await self.page.wait_for_timeout(SEARCH_CONFIG['wait_time'] * 1000)
                except:
                    logger.warning(f"无法访问 {website['name']} 的搜索URL")
                    return results
            
            # 获取页面内容
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 提取搜索结果
            result_elements = soup.select(website['results_selector'])
            
            for i, element in enumerate(result_elements[:SEARCH_CONFIG['max_results_per_site']]):
                try:
                    # 提取标题
                    title = ""
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # 提取链接
                    link = ""
                    link_elem = element.find('a')
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        if href.startswith('/'):
                            link = website['url'].rstrip('/') + href
                        elif href.startswith('http'):
                            link = href
                    
                    # 提取内容摘要
                    content = element.get_text(strip=True)
                    if len(content) > 500:
                        content = content[:500] + "..."
                    
                    # 提取图片
                    image = ""
                    img_elem = element.find('img')
                    if img_elem and img_elem.get('src'):
                        src = img_elem.get('src')
                        if src.startswith('/'):
                            image = website['url'].rstrip('/') + src
                        elif src.startswith('http'):
                            image = src
                    
                    if title or content:  # 只有当有标题或内容时才添加结果
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
                    logger.debug(f"提取搜索结果时出错: {e}")
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
                    logger.info(f"正在搜索 {website['name']}...")
                    results = await self.search_website(website, query)
                    all_results.extend(results)
                    logger.info(f"从 {website['name']} 获取到 {len(results)} 个结果")
                    
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