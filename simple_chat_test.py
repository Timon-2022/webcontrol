#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup

# 简化的配置
SEARCH_CONFIG = {
    "wait_time": 3,
    "timeout": 30,
    "headless": True,
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "chat_wait_time": 10,
    "max_chat_attempts": 3
}

# 聊天网站配置
CHAT_WEBSITES = [
    {
        "name": "ChatGPT",
        "url": "https://chat.openai.com",
        "search_selector": "textarea[data-id='root'], textarea[placeholder*='Message'], .chat-input, textarea",
        "results_selector": ".markdown, .prose, .message, .response, [data-message-author-role='assistant']",
        "chat_prompt": "请搜索并回答关于以下关键词的信息：{query}"
    },
    {
        "name": "Bing Chat",
        "url": "https://www.bing.com/chat",
        "search_selector": "textarea[placeholder*='Ask'], .chat-input, textarea",
        "results_selector": ".response, .message, .answer, [data-message-author-role='assistant']",
        "chat_prompt": "请搜索并回答关于以下关键词的信息：{query}"
    }
]

class SimpleChatScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def init_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
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
                headless=True,
                args=browser_args,
                timeout=60000,
            )
            
            context = await self.browser.new_context(
                user_agent=SEARCH_CONFIG['user_agent'],
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True,
            )
            
            self.page = await context.new_page()
            self.page.set_default_timeout(SEARCH_CONFIG['timeout'] * 1000)
            
            print("✓ 浏览器初始化成功")
            return True
            
        except Exception as e:
            print(f"✗ 浏览器初始化失败: {e}")
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
            print("✓ 浏览器已关闭")
        except Exception as e:
            print(f"✗ 关闭浏览器时出错: {e}")
    
    async def chat_search(self, website: Dict, query: str) -> List[Dict]:
        """聊天形式的搜索"""
        results = []
        try:
            print(f"正在测试 {website['name']}...")
            
            # 访问网站
            await self.page.goto(website['url'], timeout=SEARCH_CONFIG['timeout'] * 1000)
            await self.page.wait_for_timeout(SEARCH_CONFIG['wait_time'] * 1000)
            
            # 查找聊天输入框
            chat_input = None
            for selector in website['search_selector'].split(', '):
                try:
                    chat_input = await self.page.wait_for_selector(selector.strip(), timeout=10000)
                    if chat_input:
                        break
                except:
                    continue
            
            if not chat_input:
                print(f"✗ 在 {website['name']} 未找到聊天输入框")
                return results
            
            # 构造聊天提示
            chat_prompt = website['chat_prompt'].format(query=query)
            
            # 输入聊天内容
            await chat_input.fill(chat_prompt)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            await chat_input.press('Enter')
            
            # 等待回复
            print(f"等待 {website['name']} 回复...")
            await self.page.wait_for_timeout(SEARCH_CONFIG['chat_wait_time'] * 1000)
            
            # 尝试获取回复
            for attempt in range(SEARCH_CONFIG['max_chat_attempts']):
                try:
                    response_selectors = website['results_selector'].split(', ')
                    for selector in response_selectors:
                        try:
                            response_elements = await self.page.query_selector_all(selector.strip())
                            if response_elements:
                                for i, element in enumerate(response_elements):
                                    try:
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
                                            print(f"✓ 获取到 {website['name']} 回复: {response_text[:50]}...")
                                break
                        except Exception as e:
                            continue
                    
                    if results:
                        break
                    else:
                        await self.page.wait_for_timeout(3000)
                        
                except Exception as e:
                    print(f"第 {attempt + 1} 次尝试获取回复失败")
                    await self.page.wait_for_timeout(2000)
            
            if not results:
                print(f"✗ 未能从 {website['name']} 获取到回复")
                
        except Exception as e:
            print(f"✗ 聊天搜索 {website['name']} 时出错: {e}")
            
        return results

async def main():
    """主函数"""
    print("=== 聊天搜索功能测试 ===")
    print("关键词: 小鸟科技")
    
    scraper = SimpleChatScraper()
    
    try:
        # 初始化浏览器
        if not await scraper.init_browser():
            return
        
        all_results = []
        
        # 测试每个聊天网站
        for website in CHAT_WEBSITES:
            results = await scraper.chat_search(website, "小鸟科技")
            all_results.extend(results)
            await asyncio.sleep(3)
        
        # 保存结果
        if all_results:
            os.makedirs("data", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/chat_results_小鸟科技_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'query': "小鸟科技",
                    'timestamp': datetime.now().isoformat(),
                    'total_results': len(all_results),
                    'results': all_results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 测试完成！共获取到 {len(all_results)} 个聊天回复")
            print(f"结果已保存到: {filename}")
            
            # 显示结果摘要
            print("\n=== 聊天回复摘要 ===")
            for i, result in enumerate(all_results, 1):
                print(f"{i}. {result['website']}: {result['content'][:80]}...")
        else:
            print("\n✗ 未获取到任何聊天回复")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        await scraper.close_browser()

if __name__ == "__main__":
    asyncio.run(main()) 