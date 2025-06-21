#!/usr/bin/env python3
"""
持久登录状态的DeepSeek源提取器
专门解决登录状态保持问题，避免每次都需要重新登录
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

class PersistentLoginExtractor:
    """持久登录状态的源提取器"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.login_state_file = "login_state.json"
        self.user_data_dir = "./deepseek_user_data"  # 用户数据目录

    async def init_browser_with_persistent_login(self):
        """初始化浏览器并保持登录状态"""
        try:
            self.playwright = await async_playwright().start()
            
            # 使用持久化的用户数据目录
            context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 获取第一个页面或创建新页面
            if context.pages:
                self.page = context.pages[0]
            else:
                self.page = await context.new_page()
            
            logger.info("浏览器初始化成功（使用持久化用户数据）")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False

    async def check_login_status(self):
        """检查登录状态"""
        try:
            # 访问DeepSeek
            await self.page.goto("https://chat.deepseek.com", timeout=30000)
            await self.page.wait_for_timeout(3000)
            
            # 检查是否已登录（查找聊天输入框）
            try:
                chat_input = await self.page.wait_for_selector("textarea", timeout=5000)
                if chat_input:
                    logger.info("✅ 已登录状态")
                    return True
            except:
                pass
            
            # 检查是否有登录按钮
            login_selectors = [
                "text=登录",
                "text=Login", 
                "[class*='login']",
                "button:has-text('登录')",
                "a:has-text('登录')"
            ]
            
            for selector in login_selectors:
                try:
                    login_element = await self.page.query_selector(selector)
                    if login_element:
                        logger.warning("❌ 需要登录")
                        return False
                except:
                    continue
            
            logger.info("✅ 可能已登录")
            return True
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    async def manual_login_prompt(self):
        """提示手动登录"""
        print("\n" + "="*80)
        print("🔐 需要手动登录")
        print("="*80)
        print("请在打开的浏览器中手动完成登录：")
        print("1. 点击登录按钮")
        print("2. 输入用户名和密码")
        print("3. 完成任何验证步骤")
        print("4. 确保能看到聊天输入框")
        print("5. 登录完成后，按回车键继续...")
        print("="*80)
        
        # 等待用户确认
        input("按回车键继续（确保已完成登录）...")
        
        # 再次检查登录状态
        if await self.check_login_status():
            logger.info("✅ 登录确认成功")
            return True
        else:
            logger.error("❌ 登录确认失败")
            return False

    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.page and self.page.context:
                await self.page.context.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

    def is_valuable_article_url(self, url):
        """判断是否为有价值的文章页面URL"""
        if not url or len(url) < 10:
            return False
        
        url_lower = url.lower()
        
        # 过滤静态资源
        exclude_patterns = [
            '.css', '.js', '.png', '.jpg', '.svg', '.ico', '.woff', '.ttf',
            '/static/', '/assets/', '/cdn/', 'fonts.googleapis', 'widget.',
            'analytics', 'tracking', 'facebook.com', 'twitter.com',
            'deepseek.com'  # 排除DeepSeek自己的链接
        ]
        
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # 检查有价值的文章URL特征
        valuable_indicators = [
            '/article/', '/news/', '/post/', '/story/', '/detail/', '/content/',
            '.html', '.htm', '/p/', '/articles/', '/posts/', '/blog/',
            '/tech/', '/business/', '/finance/', '/company/', '/startup/',
            '/xinwen/', '/zixun/', '/baodao/', '/gonggao/'
        ]
        
        for indicator in valuable_indicators:
            if indicator in url_lower:
                return True
        
        # 检查URL结构
        parsed = urlparse(url)
        path = parsed.path
        
        if path and path.count('/') >= 2:
            if re.search(r'/\d+', path) or re.search(r'/\d{4}[/-]\d{2}', path):
                return True
            if len(path) > 10 and not path.endswith('/'):
                return True
        
        return False

    def calculate_article_score(self, url, text, title):
        """计算文章相关性得分"""
        score = 0.0
        url_lower = url.lower()
        text_lower = text.lower()
        title_lower = title.lower()
        
        # 小鸡科技相关关键词
        if '小鸡' in text_lower or 'xiaoji' in text_lower or '小鸡' in title_lower:
            score += 25.0
        if 'gamesir' in url_lower or 'gamesir' in text_lower or 'gamesir' in title_lower:
            score += 20.0
        
        # 业务关键词
        business_keywords = ['科技', '公司', '企业', '游戏', '手柄', '外设', '硬件', '控制器']
        for keyword in business_keywords:
            if keyword in text_lower or keyword in title_lower:
                score += 8.0
        
        # 权威网站
        authoritative_domains = [
            '36kr.com', 'zhihu.com', 'baidu.com', 'sohu.com', 'sina.com.cn',
            'qq.com', 'tencent.com', 'qcc.com', 'tianyancha.com', 'ithome.com'
        ]
        
        for domain in authoritative_domains:
            if domain in url_lower:
                score += 15.0
                break
        
        # URL结构评分
        if '/article/' in url_lower or '/news/' in url_lower:
            score += 12.0
        if re.search(r'/\d{4}[/-]\d{2}', url_lower):
            score += 10.0
        if url_lower.endswith('.html'):
            score += 8.0
        
        return score

    async def wait_for_response_complete(self):
        """等待回复完成"""
        logger.info("等待回复完成...")
        start_time = time.time()
        stable_count = 0
        last_content = ""
        
        while time.time() - start_time < 45:  # 增加等待时间
            try:
                elements = await self.page.query_selector_all(".ds-markdown.ds-markdown--block")
                if elements:
                    current_content = await elements[-1].inner_text()
                    if current_content == last_content:
                        stable_count += 1
                        if stable_count >= 4:
                            logger.info("回复内容已稳定")
                            break
                    else:
                        stable_count = 0
                        last_content = current_content
                
                await self.page.wait_for_timeout(2000)
            except:
                break
        
        await self.page.wait_for_timeout(5000)

    async def find_sources_info(self):
        """查找源信息"""
        try:
            selectors = [
                "text=已搜索到",
                "[class*='source']",
                "text=/已搜索到\\d+个网页/",
                "text=/搜索到\\d+/",
                "text=/\\d+个网页/"
            ]
            
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

    async def extract_article_links(self):
        """提取文章链接"""
        references = []
        
        try:
            logger.info("开始提取文章链接...")
            
            # 等待页面完全加载
            await self.page.wait_for_timeout(8000)
            
            # 多次滚动加载内容
            for i in range(6):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(1500)
            
            # 查找所有链接
            all_links = await self.page.query_selector_all("a[href]")
            logger.info(f"找到 {len(all_links)} 个链接")
            
            # 分析链接
            for i, link in enumerate(all_links):
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    # 处理相对链接
                    if href.startswith('/'):
                        href = 'https://chat.deepseek.com' + href
                    elif not href.startswith('http'):
                        continue
                    
                    text = await link.inner_text()
                    title = await link.get_attribute('title') or ''
                    
                    # 检查是否为有价值的文章URL
                    if self.is_valuable_article_url(href):
                        score = self.calculate_article_score(href, text, title)
                        
                        if score > 5.0:
                            references.append({
                                'url': href,
                                'text': text.strip()[:120],
                                'title': title.strip()[:120],
                                'score': score,
                                'domain': urlparse(href).netloc
                            })
                            
                            logger.info(f"发现文章链接: {href[:60]}... (得分: {score:.1f})")
                    
                except Exception as e:
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
            return unique_refs[:15]
            
        except Exception as e:
            logger.error(f"提取文章链接失败: {e}")
            return []

    async def run_extraction_with_persistent_login(self, query):
        """运行带持久登录的提取流程"""
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'login_required': False,
            'sources_count': 0,
            'article_references': [],
            'error': '',
            'steps': []
        }
        
        try:
            # 1. 检查登录状态
            logger.info("1. 检查登录状态...")
            if not await self.check_login_status():
                result['login_required'] = True
                if not await self.manual_login_prompt():
                    result['error'] = "登录失败"
                    return result
            result['steps'].append('确认登录状态')
            
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
                    await self.page.wait_for_timeout(5000)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    await self.page.screenshot(path=f"persistent_click_{timestamp}.png")
                    result['steps'].append('点击源链接')
                except Exception as e:
                    logger.warning(f"点击源链接失败: {e}")
            
            # 6. 提取文章链接
            logger.info("6. 提取文章链接...")
            article_refs = await self.extract_article_links()
            result['article_references'] = article_refs
            result['steps'].append('提取文章链接')
            
            result['success'] = True
            logger.info(f"提取完成: {result['sources_count']} 个源，{len(article_refs)} 个文章链接")
            
        except Exception as e:
            logger.error(f"提取过程出错: {e}")
            result['error'] = str(e)
        
        return result

    def save_and_print_result(self, result):
        """保存并打印结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"persistent_result_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存: {filename}")
        except Exception as e:
            logger.error(f"保存失败: {e}")
        
        # 打印结果
        print("\n" + "="*80)
        print("🔐 持久登录版DeepSeek源提取结果")
        print("="*80)
        print(f"查询: {result['query']}")
        print(f"成功: {'✅' if result['success'] else '❌'}")
        print(f"需要登录: {'是' if result['login_required'] else '否'}")
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
                print(f"   ⭐ 相关性得分: {ref['score']:.1f}")
                if ref['title']:
                    print(f"   📝 标题: {ref['title'][:50]}...")
                print()
        
        if result['error']:
            print(f"❌ 错误: {result['error']}")
        
        return filename


async def main():
    """主函数"""
    print("🔐 持久登录版DeepSeek源提取器")
    print("自动保持登录状态，避免重复登录")
    print("="*80)
    
    extractor = PersistentLoginExtractor()
    
    try:
        if not await extractor.init_browser_with_persistent_login():
            print("❌ 浏览器初始化失败")
            return
        
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        print(f"🎯 执行查询: {query}")
        
        result = await extractor.run_extraction_with_persistent_login(query)
        filename = extractor.save_and_print_result(result)
        
        print(f"\n✅ 详细结果已保存: {filename}")
        print("\n💡 提示：下次运行时会自动使用保存的登录状态")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await extractor.close_browser()


if __name__ == "__main__":
    asyncio.run(main())