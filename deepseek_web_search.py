#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Optional
import logging

from playwright.async_api import async_playwright, Browser, Page

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeepSeekWebSearch:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.state_file = "login_state.json"
        
    async def init_browser(self):
        """初始化浏览器，使用登录状态"""
        try:
            self.playwright = await async_playwright().start()
            
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # 有头模式，可以看到浏览器窗口
                args=browser_args,
                timeout=60000,
            )
            
            # 检查是否有登录状态文件
            if os.path.exists(self.state_file):
                logger.info(f"使用登录状态文件: {self.state_file}")
                context = await self.browser.new_context(
                    storage_state=self.state_file,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720},
                )
            else:
                logger.warning("未找到登录状态文件，将使用无登录状态")
                context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720},
                )
            
            self.page = await context.new_page()
            self.page.set_default_timeout(30000)
            
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
    
    async def chat_with_web_search(self, query: str) -> Dict:
        """与DeepSeek聊天并启用联网搜索"""
        result = {
            'website': 'DeepSeek',
            'website_url': 'https://chat.deepseek.com',
            'query': query,
            'title': 'DeepSeek 联网搜索回复',
            'link': 'https://chat.deepseek.com',
            'content': '',
            'image': '',
            'timestamp': datetime.now().isoformat(),
            'rank': 1,
            'type': 'chat_response',
            'success': False,
            'error': ''
        }
        
        if not self.page:
            result['error'] = "浏览器页面未初始化"
            return result
        
        try:
            logger.info(f"正在访问 DeepSeek...")
            await self.page.goto("https://chat.deepseek.com", timeout=30000)
            await self.page.wait_for_timeout(3000)
            
            # 检查页面标题
            title = await self.page.title()
            logger.info(f"页面标题: {title}")
            
            # 检查是否在聊天页面
            if "login" in title.lower() or "sign in" in title.lower():
                result['error'] = "需要登录，请先运行 login_manager.py 进行手动登录"
                logger.error("需要登录")
                return result
            
            # 查找聊天输入框
            chat_input = None
            selectors = [
                "textarea[placeholder*='Message']",
                "textarea[placeholder*='Send a message']",
                "textarea",
                ".chat-input",
                "[contenteditable='true']",
                "div[contenteditable='true']"
            ]
            
            for selector in selectors:
                try:
                    chat_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if chat_input:
                        logger.info(f"找到聊天输入框: {selector}")
                        break
                except:
                    continue
            
            if not chat_input:
                result['error'] = "未找到聊天输入框"
                logger.error("未找到聊天输入框")
                return result
            
            # 构造聊天提示
            chat_prompt = f"请搜索并回答关于以下关键词的信息：{query}"
            
            # 输入聊天内容
            await chat_input.fill(chat_prompt)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            await chat_input.press('Enter')
            logger.info("已发送消息，等待回复...")
            
            # 等待回复 - 增加等待时间
            await self.page.wait_for_timeout(25000)  # 等待25秒
            
            # 尝试获取回复 - 更多选择器
            response_selectors = [
                ".ds-markdown.ds-markdown--block",  # 调试找到的正确选择器
                "#root > div > div > div.c3ecdb44 > div._7780f2e > div > div._3919b83 > div > div > div.dad65929 > div._9663006",  # 用户找到的选择器
                ".markdown",
                ".prose",
                ".message",
                ".response",
                "[data-message-author-role='assistant']",
                ".text-base",
                ".chat-message",
                ".message-content",
                ".assistant-message",
                "div[data-testid*='message']",
                ".whitespace-pre-wrap",
                "[class*='message']",
                "[class*='response']"
            ]
            
            for attempt in range(5):  # 增加尝试次数
                for selector in response_selectors:
                    try:
                        response_elements = await self.page.query_selector_all(selector)
                        if response_elements:
                            # 获取最后一个回复（最新的）
                            latest_element = response_elements[-1]
                            response_text = await latest_element.inner_text()
                            
                            if response_text and len(response_text.strip()) > 10:
                                result['content'] = response_text.strip()
                                result['success'] = True
                                logger.info(f"获取到回复: {response_text[:50]}...")
                                return result
                    except Exception as e:
                        logger.debug(f"选择器 {selector} 失败: {e}")
                        continue
                
                if not result['success']:
                    logger.info(f"第 {attempt + 1} 次尝试未找到回复，继续等待...")
                    await self.page.wait_for_timeout(5000)
            
            if not result['success']:
                result['error'] = "未能获取到回复，可能需要更长时间等待"
                logger.warning("未能获取到回复")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"聊天过程中出错: {e}")
        
        return result

async def main():
    """主函数"""
    print("=== DeepSeek 联网搜索 ===")
    
    # 检查登录状态
    if not os.path.exists("login_state.json"):
        print("⚠ 未找到登录状态文件")
        print("建议先运行: python3 login_manager.py")
        print("选择选项1进行手动登录")
        print()
    
    query = input("请输入要搜索的关键词: ").strip()
    if not query:
        print("关键词不能为空！")
        return
    
    chat = DeepSeekWebSearch()
    
    try:
        # 初始化浏览器
        if not await chat.init_browser():
            print("浏览器初始化失败")
            return
        
        # 执行聊天搜索
        print(f"正在使用 DeepSeek 联网搜索关键词: {query}")
        result = await chat.chat_with_web_search(query)
        
        # 显示结果
        if result['success']:
            print(f"\n=== DeepSeek 回复 ===")
            print(result['content'])
            
            # 保存结果
            os.makedirs("data", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/deepseek_web_search_{query}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n结果已保存到: {filename}")
        else:
            print(f"\n✗ 搜索失败: {result['error']}")
            
    except Exception as e:
        print(f"程序执行出错: {e}")
    finally:
        await chat.close_browser()

if __name__ == "__main__":
    asyncio.run(main()) 