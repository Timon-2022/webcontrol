#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的DeepSeek网页源提取器
过滤资源文件，专注于真正的内容源URL
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

class OptimizedSourcesExtractor:
    """优化的DeepSeek网页源提取器"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.state_file = "login_state.json"
        
        # 定义要过滤的资源文件扩展名和域名
        self.resource_extensions = {
            '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', 
            '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.pdf'
        }
        
        self.resource_domains = {
            'fonts.googleapis.com', 'fonts.gstatic.com', 'widget.intercom.io',
            'castatic.fengkongcloud.cn', 'lf3-data.volccdn.com', 'www.w3.org',
            'cdnjs.cloudflare.com', 'ajax.googleapis.com', 'code.jquery.com'
        }
        
        self.content_indicators = {
            'www.', 'news', 'article', 'blog', 'wiki', 'baidu', 'zhihu', 
            'weibo', 'sina', 'sohu', 'qq', 'tencent', 'alibaba', 'taobao',
            'jd.com', 'tmall', 'company', 'corp', 'enterprise', 'tech',
            'xiaoji', 'gamesir', 'gamepad'
        }
    
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
    
    def is_content_url(self, url: str) -> bool:
        """判断URL是否为内容URL而非资源文件"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            
            # 过滤掉资源域名
            if any(res_domain in domain for res_domain in self.resource_domains):
                return False
            
            # 过滤掉资源文件扩展名
            if any(path.endswith(ext) for ext in self.resource_extensions):
                return False
            
            # 过滤掉明显的API或数据端点
            if any(keyword in path for keyword in ['/api/', '/data/', '/static/', '/assets/', '/js/', '/css/']):
                return False
            
            # 优先保留包含内容指示词的URL
            if any(indicator in domain or indicator in path for indicator in self.content_indicators):
                return True
            
            # 基本的URL格式检查
            if domain and len(domain) > 3 and '.' in domain:
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"URL过滤检查失败: {e}")
            return False
    
    async def wait_for_response_complete(self, timeout: int = 30):
        """等待AI回复完成"""
        print("等待AI回复完成...")
        
        await self.page.wait_for_timeout(5000)
        
        for i in range(timeout):
            try:
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
                    
                if i % 5 == 0:
                    print(f"AI正在生成回复... ({i}s)")
                
                await self.page.wait_for_timeout(1000)
                
            except Exception as e:
                logger.debug(f"检查生成状态时出错: {e}")
                await self.page.wait_for_timeout(1000)
        
        await self.page.wait_for_timeout(3000)
    
    async def find_sources_info(self) -> Dict[str, Any]:
        """查找源信息"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        await self.page.screenshot(path=f"optimized_sources_search_{timestamp}.png")
        logger.info(f"已保存截图: optimized_sources_search_{timestamp}.png")
        
        page_content = await self.page.content()
        
        # 查找源数量
        patterns = [
            r'已搜索到\s*(\d+)\s*个网页',
            r'搜索到\s*(\d+)\s*个网页',
            r'已搜索\s*(\d+)\s*个网页',
            r'搜索了\s*(\d+)\s*个网页'
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
        
        # 查找可点击的源链接元素
        sources_element = None
        
        if matched_text:
            try:
                # 尝试精确匹配
                sources_element = await self.page.query_selector(f"text={matched_text}")
                if sources_element:
                    logger.info(f"找到精确匹配的源元素: {matched_text}")
            except:
                pass
        
        # 如果精确匹配失败，尝试其他方法
        if not sources_element:
            selectors = [
                "text=已搜索到",
                "text=搜索到",
                "*:has-text('网页')",
                "button:has-text('搜索')",
                "a:has-text('搜索')"
            ]
            
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
    
    async def extract_content_urls(self) -> List[Dict[str, str]]:
        """提取内容URL，过滤掉资源文件"""
        all_urls = []
        
        # 方法1: 查找页面中的所有链接
        try:
            links = await self.page.query_selector_all("a[href]")
            for link in links:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                
                if href and href.startswith('http') and self.is_content_url(href):
                    all_urls.append({
                        'url': href,
                        'title': text.strip() if text else self._extract_title_from_url(href),
                        'method': 'page_links',
                        'score': self._calculate_relevance_score(href, text)
                    })
            
            logger.info(f"方法1: 从页面链接中找到 {len(all_urls)} 个内容URL")
        except Exception as e:
            logger.debug(f"方法1失败: {e}")
        
        # 方法2: 从页面源码中正则提取并过滤
        try:
            page_content = await self.page.content()
            url_pattern = r'https?://[^\s<>"\'`]+[^\s<>"\',.]'
            found_urls = re.findall(url_pattern, page_content)
            
            content_urls = []
            for url in found_urls:
                if self.is_content_url(url):
                    content_urls.append({
                        'url': url,
                        'title': self._extract_title_from_url(url),
                        'method': 'regex_content_filter',
                        'score': self._calculate_relevance_score(url, '')
                    })
            
            # 合并URL，避免重复
            existing_urls = {item['url'] for item in all_urls}
            for url_info in content_urls:
                if url_info['url'] not in existing_urls:
                    all_urls.append(url_info)
            
            logger.info(f"方法2: 通过正则+过滤额外找到 {len(content_urls)} 个内容URL")
        except Exception as e:
            logger.debug(f"方法2失败: {e}")
        
        # 按相关性得分排序
        all_urls.sort(key=lambda x: x['score'], reverse=True)
        
        # 去重并限制数量
        unique_urls = []
        seen_urls = set()
        for url_info in all_urls:
            if url_info['url'] not in seen_urls:
                seen_urls.add(url_info['url'])
                unique_urls.append(url_info)
                if len(unique_urls) >= 20:  # 限制最多20个URL
                    break
        
        logger.info(f"最终提取到 {len(unique_urls)} 个优质内容URL")
        return unique_urls
    
    def _calculate_relevance_score(self, url: str, text: str) -> float:
        """计算URL的相关性得分"""
        score = 0.0
        
        # URL中包含关键词
        url_lower = url.lower()
        if 'xiaoji' in url_lower or '小鸡' in url_lower:
            score += 10.0
        if 'gamesir' in url_lower or 'gamepad' in url_lower:
            score += 8.0
        if any(keyword in url_lower for keyword in ['tech', 'company', 'corp', 'enterprise']):
            score += 5.0
        
        # 文本中包含关键词
        text_lower = text.lower()
        if '小鸡' in text_lower or 'xiaoji' in text_lower:
            score += 8.0
        if any(keyword in text_lower for keyword in ['科技', '公司', '企业', 'tech', 'company']):
            score += 3.0
        
        # 域名权威性
        if any(domain in url_lower for domain in ['baidu.com', 'zhihu.com', 'wikipedia.org']):
            score += 6.0
        elif any(domain in url_lower for domain in ['.gov.', '.edu.', '.org']):
            score += 4.0
        
        # URL结构评分
        if url_lower.count('/') <= 3:  # 简洁的URL结构
            score += 2.0
        
        return score
    
    def _extract_title_from_url(self, url: str) -> str:
        """从URL中提取标题"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path
            
            if path and path != '/':
                title = f"{domain}{path[:30]}..."
            else:
                title = domain
            
            return title
        except:
            return url[:50] + "..." if len(url) > 50 else url
    
    async def search_and_extract_optimized(self, query: str) -> Dict[str, Any]:
        """优化的搜索和提取流程"""
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'content': '',
            'sources_count': 0,
            'content_urls': [],
            'filtered_count': 0,
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
            
            # 步骤6: 点击源链接（如果找到）
            if sources_info['sources_element']:
                logger.info("步骤6: 点击源链接...")
                try:
                    await sources_info['sources_element'].click()
                    await self.page.wait_for_timeout(3000)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    await self.page.screenshot(path=f"optimized_after_click_{timestamp}.png")
                    logger.info(f"已保存点击后截图: optimized_after_click_{timestamp}.png")
                    
                    result['steps_completed'].append('点击源链接')
                except Exception as e:
                    logger.warning(f"点击源链接失败: {e}")
            
            # 步骤7: 提取优化的内容URL
            logger.info("步骤7: 提取优化的内容URL...")
            content_urls = await self.extract_content_urls()
            result['content_urls'] = content_urls
            result['filtered_count'] = len(content_urls)
            result['steps_completed'].append('提取内容URL')
            
            result['success'] = True
            logger.info(f"优化提取完成: 找到 {result['sources_count']} 个源，提取 {len(content_urls)} 个内容URL")
            
        except Exception as e:
            logger.error(f"优化搜索和提取过程出错: {e}")
            result['error'] = str(e)
        
        return result
    
    def save_result(self, result: Dict[str, Any], filename: str = None) -> str:
        """保存结果"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"optimized_sources_result_{timestamp}.json"
        
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
        print("优化版DeepSeek源提取结果")
        print("="*80)
        print(f"查询: {result['query']}")
        print(f"时间: {result['timestamp']}")
        print(f"成功: {'是' if result['success'] else '否'}")
        print(f"完成步骤: {', '.join(result['steps_completed'])}")
        
        if result['success']:
            print(f"回复长度: {len(result['content'])} 字符")
            print(f"搜索网页数: {result['sources_count']}")
            print(f"提取内容URL数: {result['filtered_count']}")
            
            if result['content_urls']:
                print(f"\n优质内容源URL (按相关性排序):")
                print("-" * 80)
                for i, source in enumerate(result['content_urls'], 1):
                    print(f"{i}. {source['title']}")
                    print(f"   URL: {source['url']}")
                    print(f"   相关性得分: {source['score']:.1f}")
                    print(f"   提取方法: {source['method']}")
                    print()
        else:
            print(f"错误: {result['error']}")


async def main():
    """主函数"""
    print("优化版DeepSeek源提取器测试")
    print("="*80)
    
    extractor = OptimizedSourcesExtractor()
    
    try:
        # 初始化浏览器
        if not await extractor.init_browser():
            print("❌ 浏览器初始化失败")
            return
        
        # 执行优化的搜索和提取
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        print(f"正在执行查询: {query}")
        
        result = await extractor.search_and_extract_optimized(query)
        
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