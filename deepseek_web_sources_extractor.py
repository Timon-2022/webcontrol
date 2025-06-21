#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek网页源提取器 - 获取搜索到的网页URL列表
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
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

class DeepSeekWebSourcesExtractor:
    """DeepSeek网页源提取器"""
    
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
                headless=False,  # 有头模式，便于观察和调试
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
    
    async def search_and_extract_sources(self, query: str) -> Dict[str, Any]:
        """
        执行搜索并提取网页源
        
        Args:
            query: 搜索查询
            
        Returns:
            包含搜索结果和网页源的字典
        """
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'content': '',
            'sources_count': 0,
            'sources_urls': [],
            'error': ''
        }
        
        if not self.page:
            result['error'] = "浏览器页面未初始化"
            return result
        
        try:
            # 1. 访问DeepSeek
            logger.info("正在访问 DeepSeek...")
            await self.page.goto("https://chat.deepseek.com", timeout=30000)
            await self.page.wait_for_timeout(3000)
            
            # 检查页面标题
            title = await self.page.title()
            logger.info(f"页面标题: {title}")
            
            if "login" in title.lower() or "sign in" in title.lower():
                result['error'] = "需要登录，请先运行 login_manager.py 进行手动登录"
                return result
            
            # 2. 找到聊天输入框并发送消息
            chat_input = await self._find_chat_input()
            if not chat_input:
                result['error'] = "未找到聊天输入框"
                return result
            
            # 输入查询内容
            await chat_input.fill(query)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            await chat_input.press('Enter')
            logger.info("已发送消息，等待回复...")
            
            # 3. 等待回复完成
            await self.page.wait_for_timeout(25000)  # 等待25秒
            
            # 4. 获取回复内容
            content = await self._get_response_content()
            if content:
                result['content'] = content
                result['success'] = True
                logger.info(f"获取到回复: {content[:100]}...")
            
            # 5. 查找并点击"已搜索到XX个网页"链接
            sources_info = await self._find_and_click_sources_link()
            if sources_info:
                result['sources_count'] = sources_info['count']
                result['sources_urls'] = sources_info['urls']
                logger.info(f"成功获取 {len(sources_info['urls'])} 个网页源")
            else:
                logger.warning("未找到网页源信息")
            
            return result
            
        except Exception as e:
            logger.error(f"搜索和提取过程出错: {e}")
            result['error'] = str(e)
            return result
    
    async def _find_chat_input(self):
        """查找聊天输入框"""
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
                    return chat_input
            except:
                continue
        
        return None
    
    async def _get_response_content(self) -> str:
        """获取回复内容"""
        response_selectors = [
            ".ds-markdown.ds-markdown--block",
            "#root > div > div > div.c3ecdb44 > div._7780f2e > div > div._3919b83 > div > div > div.dad65929 > div._9663006",
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
        
        for attempt in range(5):
            for selector in response_selectors:
                try:
                    response_elements = await self.page.query_selector_all(selector)
                    if response_elements:
                        latest_element = response_elements[-1]
                        response_text = await latest_element.inner_text()
                        
                        if response_text and len(response_text.strip()) > 10:
                            return response_text.strip()
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
            
            if attempt < 4:
                logger.info(f"第 {attempt + 1} 次尝试未找到回复，继续等待...")
                await self.page.wait_for_timeout(5000)
        
        return ""
    
    async def _find_and_click_sources_link(self) -> Optional[Dict[str, Any]]:
        """查找并点击"已搜索到XX个网页"链接"""
        try:
            # 保存点击前的截图
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await self.page.screenshot(path=f"sources_before_click_{timestamp}.png")
            
            # 查找包含"已搜索到"或"搜索到"文本的元素
            sources_selectors = [
                "text=已搜索到",
                "text=搜索到", 
                "[class*='source']",
                "[class*='reference']",
                "a[href*='source']",
                "button[class*='source']",
                "div[class*='source']"
            ]
            
            sources_element = None
            sources_text = ""
            
            # 尝试不同的选择器
            for selector in sources_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if "搜索到" in text and "网页" in text:
                            sources_element = element
                            sources_text = text
                            logger.info(f"找到源链接: {text}")
                            break
                    if sources_element:
                        break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
            
            if not sources_element:
                # 尝试通过文本内容查找
                logger.info("尝试通过页面内容查找源信息...")
                page_content = await self.page.content()
                
                # 使用正则表达式查找"已搜索到XX个网页"
                pattern = r'已?搜索到\s*(\d+)\s*个?网页'
                match = re.search(pattern, page_content)
                if match:
                    count = int(match.group(1))
                    logger.info(f"从页面内容中找到源数量: {count}")
                    
                    # 尝试通过XPath查找可点击元素
                    xpath_selectors = [
                        f"//text()[contains(., '搜索到')]/parent::*",
                        f"//text()[contains(., '{count}')]/parent::*",
                        "//button[contains(text(), '搜索')]",
                        "//a[contains(text(), '搜索')]"
                    ]
                    
                    for xpath in xpath_selectors:
                        try:
                            elements = await self.page.query_selector_all(f"xpath={xpath}")
                            for element in elements:
                                text = await element.inner_text()
                                if "搜索到" in text:
                                    sources_element = element
                                    sources_text = text
                                    break
                            if sources_element:
                                break
                        except Exception as e:
                            logger.debug(f"XPath {xpath} 失败: {e}")
                            continue
                
                if not sources_element:
                    logger.warning("未找到可点击的源链接元素")
                    # 从页面内容中提取数量信息
                    if match:
                        return {
                            'count': int(match.group(1)),
                            'urls': [],
                            'note': '找到源数量但无法获取具体URL'
                        }
                    return None
            
            # 提取源数量
            count_match = re.search(r'(\d+)', sources_text)
            sources_count = int(count_match.group(1)) if count_match else 0
            
            # 点击源链接
            logger.info(f"正在点击源链接: {sources_text}")
            await sources_element.click()
            await self.page.wait_for_timeout(3000)
            
            # 保存点击后的截图
            await self.page.screenshot(path=f"sources_after_click_{timestamp}.png")
            
            # 尝试获取源URL列表
            urls = await self._extract_source_urls()
            
            return {
                'count': sources_count,
                'urls': urls,
                'clicked_text': sources_text
            }
            
        except Exception as e:
            logger.error(f"查找和点击源链接失败: {e}")
            return None
    
    async def _extract_source_urls(self) -> List[str]:
        """提取源URL列表"""
        urls = []
        
        try:
            # 等待源列表加载
            await self.page.wait_for_timeout(2000)
            
            # 尝试不同的URL选择器
            url_selectors = [
                "a[href^='http']",
                "a[href^='https']", 
                "[class*='url']",
                "[class*='link']",
                "[class*='source'] a",
                "[class*='reference'] a",
                "div[class*='source'] a[href]",
                "li a[href^='http']"
            ]
            
            for selector in url_selectors:
                try:
                    link_elements = await self.page.query_selector_all(selector)
                    for link in link_elements:
                        href = await link.get_attribute('href')
                        if href and href.startswith('http'):
                            # 获取链接文本作为标题
                            link_text = await link.inner_text()
                            urls.append({
                                'url': href,
                                'title': link_text.strip() if link_text else href,
                                'selector': selector
                            })
                    
                    if urls:
                        logger.info(f"通过选择器 {selector} 找到 {len(urls)} 个URL")
                        break
                        
                except Exception as e:
                    logger.debug(f"URL选择器 {selector} 失败: {e}")
                    continue
            
            # 如果还没找到URL，尝试从页面源码中提取
            if not urls:
                logger.info("尝试从页面源码中提取URL...")
                page_content = await self.page.content()
                
                # 使用正则表达式查找URL
                url_pattern = r'https?://[^\s<>"\']+[^\s<>"\',.]'
                found_urls = re.findall(url_pattern, page_content)
                
                # 过滤和去重
                unique_urls = list(set(found_urls))
                for url in unique_urls[:20]:  # 限制数量
                    if not any(skip in url for skip in ['javascript:', 'data:', 'blob:', 'chrome-extension:']):
                        urls.append({
                            'url': url,
                            'title': url,
                            'selector': 'regex'
                        })
            
            logger.info(f"总共提取到 {len(urls)} 个URL")
            return urls
            
        except Exception as e:
            logger.error(f"提取源URL失败: {e}")
            return []
    
    def save_sources_result(self, result: Dict[str, Any], filename: str = None) -> str:
        """保存源提取结果"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"deepseek_sources_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"源提取结果已保存: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return ""
    
    def print_sources_summary(self, result: Dict[str, Any]):
        """打印源提取摘要"""
        print("\n" + "="*60)
        print("DeepSeek网页源提取结果")
        print("="*60)
        print(f"查询: {result['query']}")
        print(f"时间: {result['timestamp']}")
        print(f"成功: {'是' if result['success'] else '否'}")
        
        if result['success']:
            print(f"回复内容长度: {len(result['content'])} 字符")
            print(f"搜索到网页数: {result['sources_count']}")
            print(f"获取到URL数: {len(result['sources_urls'])}")
            
            if result['sources_urls']:
                print(f"\n网页源列表:")
                print("-" * 60)
                for i, source in enumerate(result['sources_urls'][:10], 1):  # 只显示前10个
                    if isinstance(source, dict):
                        print(f"{i}. {source['title'][:50]}...")
                        print(f"   {source['url']}")
                    else:
                        print(f"{i}. {source}")
                
                if len(result['sources_urls']) > 10:
                    print(f"... 还有 {len(result['sources_urls']) - 10} 个URL")
        else:
            print(f"错误: {result['error']}")


async def main():
    """主函数 - 演示网页源提取功能"""
    print("DeepSeek网页源提取器演示")
    print("="*60)
    
    extractor = DeepSeekWebSourcesExtractor()
    
    try:
        # 初始化浏览器
        if not await extractor.init_browser():
            print("❌ 浏览器初始化失败")
            return
        
        # 执行搜索并提取源
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        print(f"正在搜索: {query}")
        
        result = await extractor.search_and_extract_sources(query)
        
        # 显示结果
        extractor.print_sources_summary(result)
        
        # 保存结果
        if result['success']:
            filename = extractor.save_sources_result(result)
            print(f"\n✅ 结果已保存: {filename}")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
    
    finally:
        # 关闭浏览器
        await extractor.close_browser()


if __name__ == "__main__":
    asyncio.run(main()) 