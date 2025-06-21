#!/usr/bin/env python3
"""
高级版DeepSeek源提取器
专门提取右侧参考链接区域的具体文章页面URL，而不是网站首页
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page, Browser
import re
from urllib.parse import urlparse, urljoin

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedSourcesExtractor:
    """高级版DeepSeek源提取器"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # 登录状态文件
        self.login_state_file = "login_state.json"
        
        # 常见新闻和内容网站的URL模式
        self.content_url_patterns = [
            r'.*/(article|news|post|story|content|detail|page)/.*',
            r'.*/\d{4}/\d{2}/.*',  # 日期格式URL
            r'.*/[^/]+\.html$',    # HTML文章页面
            r'.*/p/\d+',           # 知乎等平台的文章ID
            r'.*/articles?/\d+',   # 文章ID格式
            r'.*/(tech|business|finance|company)/.*',  # 分类页面
        ]
        
        # 需要过滤的无关URL模式
        self.filter_patterns = [
            r'.*\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|ttf)$',
            r'.*/static/.*',
            r'.*/assets/.*',
            r'.*/cdn/.*',
            r'.*google.*fonts.*',
            r'.*widget\..*',
            r'.*analytics.*',
            r'.*tracking.*',
        ]

    async def init_browser(self) -> bool:
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # 显示浏览器窗口便于调试
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--window-size=1920,1080'
                ]
            )
            
            # 创建页面
            self.page = await self.browser.new_page()
            
            # 设置用户代理
            await self.page.set_extra_http_headers({
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            # 加载登录状态
            await self.load_login_state()
            
            logger.info("浏览器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False

    async def load_login_state(self):
        """加载登录状态"""
        try:
            with open(self.login_state_file, 'r', encoding='utf-8') as f:
                login_data = json.load(f)
            
            if 'cookies' in login_data:
                await self.page.context.add_cookies(login_data['cookies'])
                logger.info("登录状态加载成功")
        except FileNotFoundError:
            logger.warning("未找到登录状态文件，将使用匿名模式")
        except Exception as e:
            logger.error(f"加载登录状态失败: {e}")

    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")

    def is_article_url(self, url: str) -> bool:
        """判断是否为文章页面URL"""
        if not url or len(url) < 10:
            return False
        
        # 过滤静态资源
        for pattern in self.filter_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return False
        
        # 检查是否匹配文章URL模式
        for pattern in self.content_url_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        
        # 检查URL结构特征
        parsed = urlparse(url)
        path = parsed.path
        
        # 路径包含多个层级且不是根目录
        if path and path != '/' and path.count('/') >= 2:
            return True
        
        # 包含查询参数可能是文章页面
        if parsed.query and any(param in parsed.query.lower() for param in ['id=', 'article=', 'post=']):
            return True
        
        return False

    async def wait_for_response_complete(self, timeout: int = 30):
        """等待DeepSeek回复完成"""
        logger.info("等待DeepSeek回复完成...")
        
        start_time = time.time()
        stable_count = 0
        last_content = ""
        
        while time.time() - start_time < timeout:
            try:
                # 查找最新的回复元素
                response_elements = await self.page.query_selector_all(".ds-markdown.ds-markdown--block")
                if response_elements:
                    current_content = await response_elements[-1].inner_text()
                    
                    if current_content == last_content:
                        stable_count += 1
                        if stable_count >= 3:  # 内容稳定3次，认为回复完成
                            logger.info("回复内容已稳定，认为回复完成")
                            break
                    else:
                        stable_count = 0
                        last_content = current_content
                
                await self.page.wait_for_timeout(2000)
                
            except Exception as e:
                logger.warning(f"等待回复时出错: {e}")
                break
        
        # 额外等待确保页面完全加载
        await self.page.wait_for_timeout(3000)

    async def find_sources_info(self) -> Dict[str, Any]:
        """查找源信息"""
        sources_info = {
            'sources_count': 0,
            'sources_element': None,
            'sources_text': ''
        }
        
        try:
            # 多种选择器尝试查找源信息
            selectors = [
                "text=已搜索到",
                "[class*='source']",
                "[class*='reference']",
                "text=/已搜索到\\d+个网页/",
                "text=/搜索到\\d+/",
                "[data-testid*='source']"
            ]
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if '搜索到' in text and ('网页' in text or '个' in text):
                            # 提取数字
                            import re
                            numbers = re.findall(r'\d+', text)
                            if numbers:
                                sources_info['sources_count'] = int(numbers[0])
                                sources_info['sources_element'] = element
                                sources_info['sources_text'] = text
                                logger.info(f"找到源信息: {text}")
                                return sources_info
                except:
                    continue
            
            logger.warning("未找到源信息")
            
        except Exception as e:
            logger.error(f"查找源信息时出错: {e}")
        
        return sources_info

    async def scroll_and_extract_references(self) -> List[Dict[str, Any]]:
        """滚动右侧参考链接区域并提取具体文章URL"""
        references = []
        
        try:
            logger.info("开始滚动和提取右侧参考链接...")
            
            # 查找右侧参考链接区域的多种可能选择器
            reference_area_selectors = [
                "[class*='reference']",
                "[class*='source']", 
                "[class*='citation']",
                "[class*='sidebar']",
                "[class*='panel']",
                ".ds-chat-message-content",
                "[data-testid*='reference']",
                "[data-testid*='source']"
            ]
            
            reference_area = None
            for selector in reference_area_selectors:
                try:
                    areas = await self.page.query_selector_all(selector)
                    for area in areas:
                        # 检查区域是否包含链接
                        links = await area.query_selector_all("a[href]")
                        if len(links) > 3:  # 如果包含多个链接，可能是参考区域
                            reference_area = area
                            logger.info(f"找到参考链接区域: {selector}")
                            break
                    if reference_area:
                        break
                except:
                    continue
            
            if not reference_area:
                logger.warning("未找到参考链接区域，尝试在整个页面查找链接")
                reference_area = self.page
            
            # 滚动参考区域以加载更多内容
            try:
                # 多次滚动以确保加载所有内容
                for i in range(5):
                    if self.page:
                        await self.page.evaluate("""
                            () => {
                                // 滚动到页面底部
                                window.scrollTo(0, document.body.scrollHeight);
                                
                                // 也尝试滚动参考区域
                                const referenceElements = document.querySelectorAll('[class*="reference"], [class*="source"], [class*="citation"]');
                                referenceElements.forEach(el => {
                                    if (el.scrollHeight > el.clientHeight) {
                                        el.scrollTop = el.scrollHeight;
                                    }
                                });
                            }
                        """)
                        await self.page.wait_for_timeout(1000)
                    
            except Exception as e:
                logger.warning(f"滚动时出错: {e}")
            
            # 提取所有链接
            all_links = await reference_area.query_selector_all("a[href]")
            logger.info(f"找到 {len(all_links)} 个链接")
            
            # 分析每个链接
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    title = await link.get_attribute('title') or ''
                    
                    if href and self.is_article_url(href):
                        # 计算相关性得分
                        score = self._calculate_article_relevance_score(href, text, title)
                        
                        references.append({
                            'url': href,
                            'text': text.strip()[:100],  # 限制文本长度
                            'title': title.strip()[:100],
                            'score': score,
                            'domain': urlparse(href).netloc,
                            'extraction_method': 'reference_area_scroll'
                        })
                        
                except Exception as e:
                    logger.warning(f"处理链接时出错: {e}")
                    continue
            
            # 按相关性得分排序
            references.sort(key=lambda x: x['score'], reverse=True)
            
            # 去重（基于URL）
            seen_urls = set()
            unique_references = []
            for ref in references:
                if ref['url'] not in seen_urls:
                    seen_urls.add(ref['url'])
                    unique_references.append(ref)
            
            logger.info(f"提取到 {len(unique_references)} 个唯一的文章链接")
            return unique_references[:20]  # 返回前20个最相关的
            
        except Exception as e:
            logger.error(f"滚动和提取参考链接时出错: {e}")
            return []

    def _calculate_article_relevance_score(self, url: str, text: str, title: str) -> float:
        """计算文章相关性得分"""
        score = 0.0
        url_lower = url.lower()
        text_lower = text.lower()
        title_lower = title.lower()
        
        # 关键词匹配 - 小鸡科技相关
        if '小鸡' in text_lower or 'xiaoji' in text_lower or '小鸡' in title_lower:
            score += 20.0
        if 'gamesir' in url_lower or 'gamesir' in text_lower:
            score += 15.0
        if any(keyword in text_lower or keyword in title_lower for keyword in ['科技', '公司', '企业']):
            score += 10.0
        if any(keyword in text_lower or keyword in title_lower for keyword in ['游戏', '手柄', '外设']):
            score += 8.0
        
        # 权威网站加分
        authoritative_domains = [
            '36kr.com', 'zhihu.com', 'baidu.com', 'sina.com.cn', 'sohu.com',
            'qq.com', 'tencent.com', 'alibaba.com', 'jd.com', 'tmall.com',
            'wikipedia.org', 'qcc.com', 'tianyancha.com'
        ]
        for domain in authoritative_domains:
            if domain in url_lower:
                score += 12.0
                break
        
        # 新闻和科技网站加分
        news_keywords = ['news', 'tech', 'finance', 'business', 'company', 'startup']
        for keyword in news_keywords:
            if keyword in url_lower:
                score += 5.0
        
        # URL结构评分
        if '/article/' in url_lower or '/news/' in url_lower:
            score += 8.0
        if re.search(r'/\d{4}/\d{2}/', url_lower):  # 日期格式
            score += 6.0
        if url_lower.endswith('.html'):
            score += 4.0
        
        # 文本长度合理性
        if 10 <= len(text) <= 200:
            score += 3.0
        
        return score

    async def search_and_extract_advanced(self, query: str) -> Dict[str, Any]:
        """高级搜索和提取流程"""
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'content': '',
            'sources_count': 0,
            'article_references': [],
            'total_references': 0,
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
                result['content'] = content[:500]  # 保存前500字符
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
                    await self.page.screenshot(path=f"advanced_after_click_{timestamp}.png")
                    logger.info(f"已保存点击后截图: advanced_after_click_{timestamp}.png")
                    
                    result['steps_completed'].append('点击源链接')
                except Exception as e:
                    logger.warning(f"点击源链接失败: {e}")
            
            # 步骤7: 滚动并提取参考链接
            logger.info("步骤7: 滚动并提取参考链接...")
            article_references = await self.scroll_and_extract_references()
            result['article_references'] = article_references
            result['total_references'] = len(article_references)
            result['steps_completed'].append('滚动提取参考链接')
            
            result['success'] = True
            logger.info(f"高级提取完成: 找到 {result['sources_count']} 个源，提取 {len(article_references)} 个文章链接")
            
        except Exception as e:
            logger.error(f"高级搜索和提取过程出错: {e}")
            result['error'] = str(e)
        
        return result

    def save_result(self, result: Dict[str, Any], filename: str = None) -> str:
        """保存结果"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"advanced_sources_result_{timestamp}.json"
        
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
        print("高级版DeepSeek源提取结果")
        print("="*80)
        print(f"查询: {result['query']}")
        print(f"时间: {result['timestamp']}")
        print(f"成功: {'是' if result['success'] else '否'}")
        print(f"完成步骤: {', '.join(result['steps_completed'])}")
        
        if result['success']:
            print(f"搜索网页数: {result['sources_count']}")
            print(f"提取文章链接数: {result['total_references']}")
            
            if result['article_references']:
                print(f"\n🔗 提取到的文章链接 (按相关性排序):")
                print("-" * 80)
                for i, ref in enumerate(result['article_references'][:10], 1):  # 显示前10个
                    print(f"{i}. {ref['text'][:60]}...")
                    print(f"   📰 URL: {ref['url']}")
                    print(f"   🏢 域名: {ref['domain']}")
                    print(f"   ⭐ 相关性得分: {ref['score']:.1f}")
                    if ref['title']:
                        print(f"   📝 标题: {ref['title'][:60]}...")
                    print()
        else:
            print(f"错误: {result['error']}")


async def main():
    """主函数"""
    print("高级版DeepSeek源提取器测试")
    print("="*80)
    
    extractor = AdvancedSourcesExtractor()
    
    try:
        # 初始化浏览器
        if not await extractor.init_browser():
            print("❌ 浏览器初始化失败")
            return
        
        # 执行高级搜索和提取
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        print(f"正在执行查询: {query}")
        
        result = await extractor.search_and_extract_advanced(query)
        
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