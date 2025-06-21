#!/usr/bin/env python3
"""
简化版高级源提取器测试
专门提取右侧参考链接区域的具体文章页面URL
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from playwright.async_api import async_playwright
import re
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleAdvancedExtractor:
    """简化版高级源提取器"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.login_state_file = "login_state.json"

    async def init_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.page = await self.browser.new_page()
            
            # 加载登录状态
            try:
                with open(self.login_state_file, 'r', encoding='utf-8') as f:
                    login_data = json.load(f)
                if 'cookies' in login_data:
                    await self.page.context.add_cookies(login_data['cookies'])
                    logger.info("登录状态加载成功")
            except:
                logger.warning("未找到登录状态文件")
            
            logger.info("浏览器初始化成功")
            return True
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False

    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

    def is_article_url(self, url):
        """判断是否为文章页面URL"""
        if not url or len(url) < 10:
            return False
        
        # 过滤静态资源
        static_patterns = ['.css', '.js', '.png', '.jpg', '.svg', '.ico']
        if any(url.lower().endswith(ext) for ext in static_patterns):
            return False
        
        # 过滤CDN和静态路径
        if any(path in url.lower() for path in ['/static/', '/assets/', '/cdn/', 'fonts.googleapis']):
            return False
        
        # 检查文章URL特征
        article_indicators = [
            '/article/', '/news/', '/post/', '/story/', '/detail/',
            '.html', '/p/', '/articles/', '/tech/', '/business/'
        ]
        
        url_lower = url.lower()
        for indicator in article_indicators:
            if indicator in url_lower:
                return True
        
        # 检查URL结构 - 多层路径可能是文章
        parsed = urlparse(url)
        if parsed.path and parsed.path.count('/') >= 2:
            return True
        
        return False

    def calculate_relevance_score(self, url, text, title):
        """计算相关性得分"""
        score = 0.0
        url_lower = url.lower()
        text_lower = text.lower()
        title_lower = title.lower()
        
        # 小鸡科技相关关键词
        if '小鸡' in text_lower or 'xiaoji' in text_lower:
            score += 20.0
        if 'gamesir' in url_lower or 'gamesir' in text_lower:
            score += 15.0
        if any(kw in text_lower or kw in title_lower for kw in ['科技', '公司', '企业', '游戏', '手柄']):
            score += 10.0
        
        # 权威网站
        authoritative = ['36kr.com', 'zhihu.com', 'baidu.com', 'sohu.com', 'qq.com']
        for domain in authoritative:
            if domain in url_lower:
                score += 12.0
                break
        
        # URL结构
        if '/article/' in url_lower or '/news/' in url_lower:
            score += 8.0
        if re.search(r'/\d{4}/\d{2}/', url_lower):
            score += 6.0
        
        return score

    async def wait_for_response_complete(self):
        """等待回复完成"""
        logger.info("等待回复完成...")
        start_time = time.time()
        stable_count = 0
        last_content = ""
        
        while time.time() - start_time < 30:
            try:
                elements = await self.page.query_selector_all(".ds-markdown.ds-markdown--block")
                if elements:
                    current_content = await elements[-1].inner_text()
                    if current_content == last_content:
                        stable_count += 1
                        if stable_count >= 3:
                            break
                    else:
                        stable_count = 0
                        last_content = current_content
                
                await self.page.wait_for_timeout(2000)
            except:
                break
        
        await self.page.wait_for_timeout(3000)

    async def find_sources_info(self):
        """查找源信息"""
        try:
            selectors = ["text=已搜索到", "[class*='source']", "text=/已搜索到\\d+个网页/"]
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if '搜索到' in text and ('网页' in text or '个' in text):
                            numbers = re.findall(r'\d+', text)
                            if numbers:
                                count = int(numbers[0])
                                logger.info(f"找到源信息: {text}")
                                return {'count': count, 'element': element, 'text': text}
                except:
                    continue
            
            return {'count': 0, 'element': None, 'text': ''}
        except Exception as e:
            logger.error(f"查找源信息失败: {e}")
            return {'count': 0, 'element': None, 'text': ''}

    async def extract_article_references(self):
        """提取文章引用链接"""
        references = []
        
        try:
            logger.info("开始提取文章引用链接...")
            
            # 滚动页面加载更多内容
            for i in range(5):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(1000)
            
            # 查找所有链接
            all_links = await self.page.query_selector_all("a[href]")
            logger.info(f"找到 {len(all_links)} 个链接")
            
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    title = await link.get_attribute('title') or ''
                    
                    if href and self.is_article_url(href):
                        score = self.calculate_relevance_score(href, text, title)
                        
                        references.append({
                            'url': href,
                            'text': text.strip()[:100],
                            'title': title.strip()[:100],
                            'score': score,
                            'domain': urlparse(href).netloc
                        })
                except:
                    continue
            
            # 排序和去重
            references.sort(key=lambda x: x['score'], reverse=True)
            
            seen_urls = set()
            unique_refs = []
            for ref in references:
                if ref['url'] not in seen_urls:
                    seen_urls.add(ref['url'])
                    unique_refs.append(ref)
            
            logger.info(f"提取到 {len(unique_refs)} 个唯一文章链接")
            return unique_refs[:15]  # 返回前15个最相关的
            
        except Exception as e:
            logger.error(f"提取文章引用失败: {e}")
            return []

    async def run_extraction(self, query):
        """运行提取流程"""
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'sources_count': 0,
            'article_references': [],
            'error': '',
            'steps': []
        }
        
        try:
            # 1. 访问DeepSeek
            logger.info("1. 访问DeepSeek...")
            await self.page.goto("https://chat.deepseek.com", timeout=30000)
            await self.page.wait_for_timeout(3000)
            result['steps'].append('访问DeepSeek')
            
            # 2. 发送查询
            logger.info("2. 发送查询...")
            chat_input = await self.page.wait_for_selector("textarea", timeout=10000)
            await chat_input.fill(query)
            await chat_input.press('Enter')
            result['steps'].append('发送查询')
            
            # 3. 等待回复完成
            logger.info("3. 等待回复完成...")
            await self.wait_for_response_complete()
            result['steps'].append('等待回复完成')
            
            # 4. 查找源信息
            logger.info("4. 查找源信息...")
            sources_info = await self.find_sources_info()
            result['sources_count'] = sources_info['count']
            result['steps'].append('查找源信息')
            
            # 5. 点击源链接
            if sources_info['element']:
                logger.info("5. 点击源链接...")
                try:
                    await sources_info['element'].click()
                    await self.page.wait_for_timeout(3000)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    await self.page.screenshot(path=f"advanced_click_{timestamp}.png")
                    result['steps'].append('点击源链接')
                except Exception as e:
                    logger.warning(f"点击失败: {e}")
            
            # 6. 提取文章引用
            logger.info("6. 提取文章引用...")
            article_refs = await self.extract_article_references()
            result['article_references'] = article_refs
            result['steps'].append('提取文章引用')
            
            result['success'] = True
            logger.info(f"提取完成: {result['sources_count']} 个源，{len(article_refs)} 个文章链接")
            
        except Exception as e:
            logger.error(f"提取过程出错: {e}")
            result['error'] = str(e)
        
        return result

    def save_and_print_result(self, result):
        """保存并打印结果"""
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"advanced_result_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存: {filename}")
        except Exception as e:
            logger.error(f"保存失败: {e}")
        
        # 打印结果
        print("\n" + "="*80)
        print("🚀 高级版DeepSeek源提取结果")
        print("="*80)
        print(f"查询: {result['query']}")
        print(f"成功: {'✅' if result['success'] else '❌'}")
        print(f"搜索网页数: {result['sources_count']}")
        print(f"提取文章数: {len(result['article_references'])}")
        print(f"完成步骤: {' → '.join(result['steps'])}")
        
        if result['article_references']:
            print(f"\n📄 提取到的文章链接 (按相关性排序):")
            print("-" * 80)
            for i, ref in enumerate(result['article_references'][:10], 1):
                print(f"{i}. {ref['text'][:50]}...")
                print(f"   🔗 URL: {ref['url']}")
                print(f"   🏢 域名: {ref['domain']}")
                print(f"   ⭐ 得分: {ref['score']:.1f}")
                if ref['title']:
                    print(f"   📝 标题: {ref['title'][:50]}...")
                print()
        
        if result['error']:
            print(f"❌ 错误: {result['error']}")
        
        return filename


async def main():
    """主函数"""
    print("🔍 高级版DeepSeek源提取器")
    print("专门提取具体文章页面URL，而非网站首页")
    print("="*80)
    
    extractor = SimpleAdvancedExtractor()
    
    try:
        if not await extractor.init_browser():
            print("❌ 浏览器初始化失败")
            return
        
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        print(f"🎯 执行查询: {query}")
        
        result = await extractor.run_extraction(query)
        filename = extractor.save_and_print_result(result)
        
        print(f"\n✅ 详细结果已保存: {filename}")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
    
    finally:
        await extractor.close_browser()


if __name__ == "__main__":
    asyncio.run(main()) 