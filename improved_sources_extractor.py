#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的DeepSeek网页源提取器
基于之前的测试经验，优化源链接查找策略
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

class ImprovedSourcesExtractor:
    """改进的DeepSeek网页源提取器"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.state_file = "login_state.json"
        
    async def init_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-dev-shm-usage'],
                timeout=60000,
            )
            
            if os.path.exists(self.state_file):
                logger.info(f"使用登录状态文件: {self.state_file}")
                context = await self.browser.new_context(
                    storage_state=self.state_file,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720},
                )
            else:
                logger.warning("未找到登录状态文件")
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
    
    async def wait_for_response_complete(self, timeout: int = 30):
        """等待AI回复完成"""
        print("等待AI回复完成...")
        
        # 等待一段时间让回复开始
        await self.page.wait_for_timeout(5000)
        
        # 检查是否有"停止生成"按钮，如果有说明还在生成
        for i in range(timeout):
            try:
                # 查找停止生成按钮
                stop_buttons = await self.page.query_selector_all("button")
                is_generating = False
                
                for button in stop_buttons:
                    text = await button.inner_text()
                    if "停止" in text or "stop" in text.lower():
                        is_generating = True
                        break
                
                if not is_generating:
                    logger.info("AI回复已完成")
                    break
                    
                if i % 5 == 0:  # 每5秒打印一次状态
                    print(f"AI正在生成回复... ({i}s)")
                
                await self.page.wait_for_timeout(1000)
                
            except Exception as e:
                logger.debug(f"检查生成状态时出错: {e}")
                await self.page.wait_for_timeout(1000)
        
        # 额外等待一段时间确保完全加载
        await self.page.wait_for_timeout(3000)
    
    async def find_sources_info(self) -> Dict[str, Any]:
        """查找源信息"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存当前页面截图
        await self.page.screenshot(path=f"sources_search_{timestamp}.png")
        logger.info(f"已保存截图: sources_search_{timestamp}.png")
        
        # 获取页面内容进行分析
        page_content = await self.page.content()
        
        # 方法1: 查找"已搜索到XX个网页"模式
        patterns = [
            r'已搜索到\s*(\d+)\s*个网页',
            r'搜索到\s*(\d+)\s*个网页',
            r'已搜索\s*(\d+)\s*个网页',
            r'搜索了\s*(\d+)\s*个网页',
            r'(\d+)\s*个网页',
            r'找到\s*(\d+)\s*个相关网页'
        ]
        
        sources_count = 0
        matched_text = ""
        
        for pattern in patterns:
            matches = re.findall(pattern, page_content)
            if matches:
                sources_count = int(matches[0])
                matched_text = re.search(pattern, page_content).group(0)
                logger.info(f"找到源数量: {sources_count} ({matched_text})")
                break
        
        # 方法2: 查找可点击的源链接元素
        sources_element = None
        
        # 尝试不同的选择器策略
        selectors = [
            # 直接文本匹配
            f"text={matched_text}" if matched_text else None,
            "text=已搜索到",
            "text=搜索到",
            # 包含数字的元素
            "*:has-text('" + str(sources_count) + "')" if sources_count > 0 else None,
            # 可能的按钮或链接
            "button:has-text('搜索')",
            "a:has-text('搜索')",
            "div:has-text('搜索')",
            # CSS类选择器
            "[class*='source']",
            "[class*='reference']",
            "[class*='link']"
        ]
        
        # 过滤掉None值
        selectors = [s for s in selectors if s]
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if any(keyword in text for keyword in ['搜索到', '网页', str(sources_count)]):
                        sources_element = element
                        logger.info(f"找到源元素: {text} (选择器: {selector})")
                        break
                if sources_element:
                    break
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue
        
        return {
            'sources_count': sources_count,
            'matched_text': matched_text,
            'sources_element': sources_element,
            'timestamp': timestamp
        }
    
    async def click_sources_and_extract_urls(self, sources_element) -> List[Dict[str, str]]:
        """点击源链接并提取URL"""
        urls = []
        
        try:
            # 点击源元素
            logger.info("正在点击源链接...")
            await sources_element.click()
            await self.page.wait_for_timeout(3000)
            
            # 保存点击后的截图
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await self.page.screenshot(path=f"after_sources_click_{timestamp}.png")
            logger.info(f"已保存点击后截图: after_sources_click_{timestamp}.png")
            
            # 等待可能的弹窗或新内容加载
            await self.page.wait_for_timeout(2000)
            
            # 尝试多种方法提取URL
            urls = await self._extract_urls_multiple_methods()
            
        except Exception as e:
            logger.error(f"点击源链接失败: {e}")
        
        return urls
    
    async def _extract_urls_multiple_methods(self) -> List[Dict[str, str]]:
        """使用多种方法提取URL"""
        urls = []
        
        # 方法1: 查找所有HTTP链接
        try:
            links = await self.page.query_selector_all("a[href^='http']")
            for link in links:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                if href and href.startswith('http'):
                    urls.append({
                        'url': href,
                        'title': text.strip() if text else href,
                        'method': 'direct_links'
                    })
            logger.info(f"方法1: 找到 {len(urls)} 个直接链接")
        except Exception as e:
            logger.debug(f"方法1失败: {e}")
        
        # 方法2: 从页面源码中正则提取
        if len(urls) < 5:  # 如果直接链接太少，尝试正则提取
            try:
                page_content = await self.page.content()
                url_pattern = r'https?://[^\s<>"\'`]+[^\s<>"\',.]'
                found_urls = re.findall(url_pattern, page_content)
                
                # 过滤和去重
                unique_urls = list(set(found_urls))
                for url in unique_urls[:30]:  # 限制数量
                    if not any(skip in url for skip in [
                        'javascript:', 'data:', 'blob:', 'chrome-extension:',
                        'localhost', '127.0.0.1', 'deepseek.com'
                    ]):
                        urls.append({
                            'url': url,
                            'title': self._extract_title_from_url(url),
                            'method': 'regex_extraction'
                        })
                
                logger.info(f"方法2: 通过正则表达式额外找到 {len(unique_urls)} 个URL")
            except Exception as e:
                logger.debug(f"方法2失败: {e}")
        
        # 方法3: 查找特定的源容器
        try:
            source_containers = await self.page.query_selector_all("[class*='source'], [class*='reference'], [class*='citation']")
            for container in source_containers:
                container_links = await container.query_selector_all("a[href]")
                for link in container_links:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and href.startswith('http'):
                        urls.append({
                            'url': href,
                            'title': text.strip() if text else href,
                            'method': 'source_containers'
                        })
            logger.info(f"方法3: 从源容器中找到额外链接")
        except Exception as e:
            logger.debug(f"方法3失败: {e}")
        
        # 去重
        seen_urls = set()
        unique_urls = []
        for url_info in urls:
            if url_info['url'] not in seen_urls:
                seen_urls.add(url_info['url'])
                unique_urls.append(url_info)
        
        logger.info(f"总共提取到 {len(unique_urls)} 个唯一URL")
        return unique_urls
    
    def _extract_title_from_url(self, url: str) -> str:
        """从URL中提取标题"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path
            
            # 简单的标题生成
            if path and path != '/':
                title = f"{domain}{path[:30]}..."
            else:
                title = domain
            
            return title
        except:
            return url[:50] + "..." if len(url) > 50 else url
    
    async def search_and_extract_complete(self, query: str) -> Dict[str, Any]:
        """完整的搜索和提取流程"""
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'content': '',
            'sources_count': 0,
            'sources_urls': [],
            'error': '',
            'steps_completed': []
        }
        
        try:
            # 步骤1: 访问DeepSeek
            logger.info("步骤1: 访问DeepSeek...")
            await self.page.goto("https://chat.deepseek.com", timeout=30000)
            await self.page.wait_for_timeout(3000)
            result['steps_completed'].append('访问DeepSeek')
            
            # 步骤2: 发送查询
            logger.info("步骤2: 发送查询...")
            chat_input = await self.page.wait_for_selector("textarea", timeout=10000)
            await chat_input.fill(query)
            await chat_input.press('Enter')
            result['steps_completed'].append('发送查询')
            
            # 步骤3: 等待回复完成
            logger.info("步骤3: 等待回复完成...")
            await self.wait_for_response_complete()
            result['steps_completed'].append('等待回复完成')
            
            # 步骤4: 获取回复内容
            logger.info("步骤4: 获取回复内容...")
            response_elements = await self.page.query_selector_all(".ds-markdown.ds-markdown--block")
            if response_elements:
                latest_response = response_elements[-1]
                content = await latest_response.inner_text()
                result['content'] = content
                result['steps_completed'].append('获取回复内容')
            
            # 步骤5: 查找源信息
            logger.info("步骤5: 查找源信息...")
            sources_info = await self.find_sources_info()
            result['sources_count'] = sources_info['sources_count']
            result['steps_completed'].append('查找源信息')
            
            # 步骤6: 提取URL
            if sources_info['sources_element']:
                logger.info("步骤6: 点击源链接并提取URL...")
                urls = await self.click_sources_and_extract_urls(sources_info['sources_element'])
                result['sources_urls'] = urls
                result['steps_completed'].append('提取URL')
            else:
                logger.warning("未找到可点击的源元素，尝试直接提取URL...")
                urls = await self._extract_urls_multiple_methods()
                result['sources_urls'] = urls
                result['steps_completed'].append('直接提取URL')
            
            result['success'] = True
            logger.info(f"搜索和提取完成: 找到 {result['sources_count']} 个源，提取 {len(result['sources_urls'])} 个URL")
            
        except Exception as e:
            logger.error(f"搜索和提取过程出错: {e}")
            result['error'] = str(e)
        
        return result
    
    def save_result(self, result: Dict[str, Any], filename: str = None) -> str:
        """保存结果"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"improved_sources_result_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return ""
    
    def print_result_summary(self, result: Dict[str, Any]):
        """打印结果摘要"""
        print("\n" + "="*80)
        print("改进版DeepSeek源提取结果")
        print("="*80)
        print(f"查询: {result['query']}")
        print(f"时间: {result['timestamp']}")
        print(f"成功: {'是' if result['success'] else '否'}")
        print(f"完成步骤: {', '.join(result['steps_completed'])}")
        
        if result['success']:
            print(f"回复长度: {len(result['content'])} 字符")
            print(f"搜索网页数: {result['sources_count']}")
            print(f"提取URL数: {len(result['sources_urls'])}")
            
            if result['sources_urls']:
                print(f"\n提取的网页源:")
                print("-" * 80)
                for i, source in enumerate(result['sources_urls'][:10], 1):
                    print(f"{i}. {source['title'][:60]}...")
                    print(f"   {source['url']}")
                    print(f"   (提取方法: {source['method']})")
                    print()
                
                if len(result['sources_urls']) > 10:
                    print(f"... 还有 {len(result['sources_urls']) - 10} 个URL")
        else:
            print(f"错误: {result['error']}")


async def main():
    """主函数"""
    print("改进版DeepSeek源提取器测试")
    print("="*80)
    
    extractor = ImprovedSourcesExtractor()
    
    try:
        # 初始化浏览器
        if not await extractor.init_browser():
            print("❌ 浏览器初始化失败")
            return
        
        # 执行完整的搜索和提取
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        print(f"正在执行查询: {query}")
        
        result = await extractor.search_and_extract_complete(query)
        
        # 显示结果
        extractor.print_result_summary(result)
        
        # 保存结果
        filename = extractor.save_result(result)
        print(f"\n✅ 详细结果已保存: {filename}")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
    
    finally:
        # 关闭浏览器
        await extractor.close_browser()


if __name__ == "__main__":
    asyncio.run(main()) 