#!/usr/bin/env python3
"""
全面参考来源提取器
系统性地滚动并点击右侧参考区域的所有来源，获取完整的参考网页信息
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

async def extract_page_info(page):
    """提取页面的详细信息"""
    try:
        # 获取基本信息
        url = page.url
        title = await page.title()
        
        # 获取描述
        description = ""
        try:
            desc_element = await page.query_selector('meta[name="description"]')
            if desc_element:
                description = await desc_element.get_attribute('content') or ""
        except:
            pass
        
        # 获取关键词
        keywords = ""
        try:
            keywords_element = await page.query_selector('meta[name="keywords"]')
            if keywords_element:
                keywords = await keywords_element.get_attribute('keywords') or ""
        except:
            pass
        
        # 获取H1和H2标题
        h1_texts = []
        h2_texts = []
        try:
            h1_elements = await page.query_selector_all('h1')
            for h1 in h1_elements:
                text = await h1.inner_text()
                if text.strip():
                    h1_texts.append(text.strip())
            
            h2_elements = await page.query_selector_all('h2')
            for h2 in h2_elements:
                text = await h2.inner_text()
                if text.strip():
                    h2_texts.append(text.strip())
        except:
            pass
        
        # 获取主要内容
        article_content = ""
        content_selectors = [
            'article', 'main', '.content', '.article', '.post', 
            '.entry-content', '.post-content', '.article-content',
            '[class*="content"]', '[class*="article"]'
        ]
        
        for selector in content_selectors:
            try:
                content_element = await page.query_selector(selector)
                if content_element:
                    content_text = await content_element.inner_text()
                    if len(content_text) > len(article_content):
                        article_content = content_text
            except:
                continue
        
        # 如果没有找到主要内容，获取body内容
        if not article_content:
            try:
                body_element = await page.query_selector('body')
                if body_element:
                    article_content = await body_element.inner_text()
            except:
                pass
        
        # 统计链接和图片数量
        links_count = len(await page.query_selector_all('a'))
        images_count = len(await page.query_selector_all('img'))
        
        # 获取域名
        domain = ""
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
        except:
            pass
        
        return {
            "url": url,
            "title": title,
            "description": description,
            "keywords": keywords,
            "h1_texts": h1_texts,
            "h2_texts": h2_texts,
            "article_content": article_content[:2000],  # 限制长度
            "links_count": links_count,
            "images_count": images_count,
            "domain": domain
        }
    except Exception as e:
        print(f"提取页面信息出错: {e}")
        return {}

async def scroll_and_find_sources(page):
    """滚动右侧区域并查找所有可点击的来源"""
    print("开始滚动右侧区域查找参考来源...")
    
    # 查找右侧参考区域
    right_panel_selectors = [
        '[class*="search-view"]',
        '[class*="reference"]', 
        '[class*="source"]',
        '[class*="result"]'
    ]
    
    # 先尝试滚动整个页面，然后专门滚动右侧区域
    for i in range(5):  # 滚动5次，确保加载所有内容
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        
        # 尝试滚动右侧区域
        try:
            await page.evaluate("""
                () => {
                    // 查找右侧区域并滚动
                    const rightElements = document.querySelectorAll('[class*="search-view"], [class*="reference"], [class*="source"]');
                    rightElements.forEach(el => {
                        if (el.scrollTop !== undefined) {
                            el.scrollTop = el.scrollHeight;
                        }
                    });
                }
            """)
        except:
            pass
        
        await page.wait_for_timeout(1000)
    
    # 查找所有可能的参考来源元素
    sources = await page.evaluate("""
        () => {
            const results = [];
            const allElements = document.querySelectorAll('*');
            
            allElements.forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                
                // 重点关注右侧区域 (x > 700)
                if (rect.x > 700 && rect.width > 50 && rect.height > 15) {
                    const text = el.innerText || el.textContent || '';
                    
                    // 判断是否是标题或链接
                    const isRelevant = (
                        // 包含相关关键词
                        (text.includes('小鸡') || text.includes('盖世') || text.includes('GameSir') || 
                         text.includes('科技') || text.includes('网络') || text.includes('公司') ||
                         text.includes('游戏') || text.includes('外设') || text.includes('手柄')) ||
                        // 或者是标题样式的元素
                        (el.tagName === 'H1' || el.tagName === 'H2' || el.tagName === 'H3' ||
                         el.className.includes('title') || el.className.includes('heading')) ||
                        // 或者是可点击的元素
                        (el.tagName === 'A' || el.onclick !== null || 
                         window.getComputedStyle(el).cursor === 'pointer')
                    );
                    
                    if (isRelevant && text.length > 5 && text.length < 300) {
                        results.push({
                            index: index,
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            text: text.trim(),
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            href: el.href || null,
                            cursor: window.getComputedStyle(el).cursor,
                            isClickable: (
                                el.tagName === 'A' || el.onclick !== null ||
                                window.getComputedStyle(el).cursor === 'pointer' ||
                                el.querySelector('a') !== null
                            )
                        });
                    }
                }
            });
            
            // 去重并按相关性排序
            const unique = results.filter((item, index, self) => 
                index === self.findIndex(t => t.text === item.text)
            );
            
            return unique.sort((a, b) => {
                const scoreA = (a.isClickable ? 10 : 0) + 
                              (a.text.includes('小鸡') ? 5 : 0) +
                              (a.tagName === 'A' ? 3 : 0);
                const scoreB = (b.isClickable ? 10 : 0) + 
                              (b.text.includes('小鸡') ? 5 : 0) +
                              (b.tagName === 'A' ? 3 : 0);
                return scoreB - scoreA;
            });
        }
    """)
    
    print(f"找到 {len(sources)} 个潜在的参考来源")
    return sources

async def main():
    """主函数"""
    print("🎯 全面参考来源提取器")
    print("系统性地滚动并点击右侧参考区域的所有来源")
    print("="*80)
    
    playwright = None
    context = None
    
    try:
        # 1. 启动浏览器
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir="./deepseek_user_data",
            headless=False,
            viewport={'width': 1920, 'height': 1080}
        )
        
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        # 2. 访问DeepSeek
        print("2. 访问DeepSeek...")
        await page.goto("https://chat.deepseek.com", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 3. 发送查询
        print("3. 发送查询...")
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        
        # 先点击联网搜索
        try:
            web_search_button = await page.wait_for_selector("text=联网搜索", timeout=10000)
            await web_search_button.click()
            print("✅ 已点击联网搜索")
            await page.wait_for_timeout(2000)
        except:
            print("⚠️ 未找到联网搜索按钮，继续...")
        
        # 输入查询
        chat_input = await page.wait_for_selector("textarea", timeout=10000)
        await chat_input.fill(query)
        await chat_input.press('Enter')
        
        # 4. 等待回复完成
        print("4. 等待回复完成...")
        await page.wait_for_timeout(45000)  # 等待45秒确保完全加载
        
        # 5. 滚动并查找所有参考来源
        print("5. 滚动并查找所有参考来源...")
        sources = await scroll_and_find_sources(page)
        
        # 6. 保存截图
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        await page.screenshot(path=f"comprehensive_sources_{timestamp}.png", full_page=True)
        print(f"✅ 全页截图已保存: comprehensive_sources_{timestamp}.png")
        
        # 7. 逐个点击参考来源
        print(f"7. 开始点击 {len(sources)} 个参考来源...")
        
        extracted_articles = []
        successful_clicks = 0
        
        for i, source in enumerate(sources[:20]):  # 限制前20个最相关的
            try:
                print(f"\n点击来源 {i+1}/{min(20, len(sources))}: {source['text'][:60]}...")
                
                # 记录点击前状态
                initial_pages = len(context.pages)
                current_url = page.url
                
                # 尝试多种点击方式
                click_success = False
                
                # 方法1: 坐标点击
                try:
                    await page.mouse.click(
                        source['x'] + source['width']/2, 
                        source['y'] + source['height']/2
                    )
                    await page.wait_for_timeout(3000)
                    
                    # 检查是否有新页面或URL变化
                    if len(context.pages) > initial_pages or page.url != current_url:
                        click_success = True
                        print("  ✅ 坐标点击成功")
                except Exception as e1:
                    print(f"  ❌ 坐标点击失败: {e1}")
                
                # 方法2: JavaScript点击
                if not click_success:
                    try:
                        await page.evaluate(f"""
                            () => {{
                                const elements = document.querySelectorAll('*');
                                for (let el of elements) {{
                                    const rect = el.getBoundingClientRect();
                                    if (Math.abs(rect.x - {source['x']}) < 10 && 
                                        Math.abs(rect.y - {source['y']}) < 10) {{
                                        el.click();
                                        break;
                                    }}
                                }}
                            }}
                        """)
                        await page.wait_for_timeout(3000)
                        
                        if len(context.pages) > initial_pages or page.url != current_url:
                            click_success = True
                            print("  ✅ JavaScript点击成功")
                    except Exception as e2:
                        print(f"  ❌ JavaScript点击失败: {e2}")
                
                # 处理点击结果
                if click_success:
                    successful_clicks += 1
                    
                    # 检查是否打开了新标签页
                    if len(context.pages) > initial_pages:
                        # 切换到新标签页
                        new_page = context.pages[-1]
                        await new_page.wait_for_load_state('networkidle', timeout=10000)
                        
                        # 提取页面信息
                        article_data = await extract_page_info(new_page)
                        
                        extracted_articles.append({
                            "source_index": i + 1,
                            "source_text": source['text'],
                            "click_success": True,
                            "result_type": "new_tab",
                            "article_data": article_data
                        })
                        
                        print(f"  📄 新标签页: {article_data.get('title', 'Unknown')}")
                        print(f"  🔗 URL: {article_data.get('url', 'Unknown')}")
                        
                        # 关闭新标签页，回到原页面
                        await new_page.close()
                        
                    elif page.url != current_url:
                        # 当前页面URL变化
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        
                        # 提取页面信息
                        article_data = await extract_page_info(page)
                        
                        extracted_articles.append({
                            "source_index": i + 1,
                            "source_text": source['text'],
                            "click_success": True,
                            "result_type": "page_navigation",
                            "article_data": article_data
                        })
                        
                        print(f"  📄 页面跳转: {article_data.get('title', 'Unknown')}")
                        print(f"  🔗 URL: {article_data.get('url', 'Unknown')}")
                        
                        # 返回原页面
                        await page.go_back()
                        await page.wait_for_timeout(3000)
                else:
                    extracted_articles.append({
                        "source_index": i + 1,
                        "source_text": source['text'],
                        "click_success": False,
                        "result_type": "no_response",
                        "article_data": {}
                    })
                    print("  ❌ 点击无响应")
                
                # 短暂延迟避免过快操作
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"  ❌ 处理来源时出错: {e}")
                extracted_articles.append({
                    "source_index": i + 1,
                    "source_text": source['text'],
                    "click_success": False,
                    "result_type": "error",
                    "error": str(e),
                    "article_data": {}
                })
        
        # 8. 保存结果
        result = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "total_sources_found": len(sources),
            "sources_attempted": min(20, len(sources)),
            "successful_clicks": successful_clicks,
            "extracted_articles": extracted_articles,
            "all_sources_info": sources
        }
        
        result_filename = f"comprehensive_sources_result_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 结果已保存到: {result_filename}")
        print(f"📊 统计信息:")
        print(f"   - 找到参考来源: {len(sources)} 个")
        print(f"   - 尝试点击: {min(20, len(sources))} 个")
        print(f"   - 成功点击: {successful_clicks} 个")
        print(f"   - 成功率: {successful_clicks/min(20, len(sources))*100:.1f}%")
        
        return result
        
    except Exception as e:
        print(f"❌ 执行过程中出错: {e}")
        return None
        
    finally:
        if context:
            await context.close()
        if playwright:
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main()) 