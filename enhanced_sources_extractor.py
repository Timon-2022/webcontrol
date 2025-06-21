#!/usr/bin/env python3
"""
增强版参考来源提取器
系统性地滚动并点击右侧参考区域的所有来源，获取完整的参考网页信息
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urlparse

async def extract_page_summary(page, max_content_length=500):
    """提取页面的简要信息，生成100字左右的简报"""
    try:
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
        
        # 获取主要内容
        content = ""
        content_selectors = [
            'article', 'main', '.content', '.article', '.post', 
            '.entry-content', '.post-content', '.article-content'
        ]
        
        for selector in content_selectors:
            try:
                content_element = await page.query_selector(selector)
                if content_element:
                    content_text = await content_element.inner_text()
                    if len(content_text) > len(content):
                        content = content_text
            except:
                continue
        
        # 如果没有找到主要内容，获取body内容
        if not content:
            try:
                body_element = await page.query_selector('body')
                if body_element:
                    content = await body_element.inner_text()
            except:
                pass
        
        # 生成简报（100字左右）
        summary = ""
        if description:
            summary = description[:100] + "..." if len(description) > 100 else description
        elif content:
            # 提取前100个字符作为简报
            content_clean = content.replace('\n', ' ').replace('\t', ' ').strip()
            summary = content_clean[:100] + "..." if len(content_clean) > 100 else content_clean
        
        # 获取域名
        domain = ""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
        except:
            pass
        
        return {
            "url": url,
            "title": title,
            "domain": domain,
            "summary": summary,
            "content_length": len(content)
        }
    except Exception as e:
        print(f"提取页面信息出错: {e}")
        return {"url": page.url, "title": "", "domain": "", "summary": "", "content_length": 0}

async def scroll_right_panel(page):
    """系统性地滚动右侧参考区域"""
    print("开始滚动右侧参考区域...")
    
    # 多次滚动确保加载所有内容
    for scroll_round in range(8):  # 增加滚动次数
        print(f"  滚动轮次 {scroll_round + 1}/8")
        
        # 滚动整个页面
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
        
        # 专门滚动右侧区域
        try:
            await page.evaluate("""
                () => {
                    // 查找并滚动右侧区域
                    const rightSelectors = [
                        '[class*="search-view"]',
                        '[class*="reference"]', 
                        '[class*="source"]',
                        '[class*="result"]',
                        '[class*="panel"]'
                    ];
                    
                    rightSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.x > 600 && el.scrollHeight > el.clientHeight) {
                                el.scrollTop = el.scrollHeight;
                            }
                        });
                    });
                    
                    // 通用滚动右侧区域
                    const allElements = document.querySelectorAll('*');
                    allElements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.x > 600 && rect.width > 300 && el.scrollHeight > el.clientHeight) {
                            el.scrollTop = el.scrollHeight;
                        }
                    });
                }
            """)
        except Exception as e:
            print(f"  滚动右侧区域时出错: {e}")
        
        await page.wait_for_timeout(1000)
    
    print("✅ 滚动完成")

async def find_all_sources(page):
    """查找所有可能的参考来源"""
    print("查找所有参考来源...")
    
    sources = await page.evaluate("""
        () => {
            const results = [];
            const allElements = document.querySelectorAll('*');
            
            allElements.forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                
                // 重点关注右侧区域 (x > 650)
                if (rect.x > 650 && rect.width > 80 && rect.height > 10 && rect.height < 200) {
                    const text = (el.innerText || el.textContent || '').trim();
                    
                    if (text.length > 8 && text.length < 500) {
                        // 计算相关性得分
                        let relevanceScore = 0;
                        
                        // 关键词匹配
                        const keywords = ['小鸡', '盖世', 'GameSir', '科技', '网络', '公司', '游戏', '外设', '手柄'];
                        keywords.forEach(keyword => {
                            if (text.includes(keyword)) relevanceScore += 3;
                        });
                        
                        // 元素类型加分
                        if (el.tagName === 'A') relevanceScore += 5;
                        if (el.tagName.match(/^H[1-6]$/)) relevanceScore += 4;
                        if (el.className.includes('title')) relevanceScore += 4;
                        if (el.className.includes('link')) relevanceScore += 3;
                        
                        // 可点击性加分
                        if (el.onclick !== null) relevanceScore += 3;
                        if (window.getComputedStyle(el).cursor === 'pointer') relevanceScore += 3;
                        if (el.querySelector('a')) relevanceScore += 2;
                        
                        // 位置加分（更靠右的元素可能是参考来源）
                        if (rect.x > 800) relevanceScore += 2;
                        if (rect.x > 900) relevanceScore += 1;
                        
                        if (relevanceScore > 0) {
                            results.push({
                                index: index,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                text: text,
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id,
                                href: el.href || null,
                                cursor: window.getComputedStyle(el).cursor,
                                relevanceScore: relevanceScore,
                                isClickable: (
                                    el.tagName === 'A' || 
                                    el.onclick !== null ||
                                    window.getComputedStyle(el).cursor === 'pointer' ||
                                    el.querySelector('a') !== null
                                )
                            });
                        }
                    }
                }
            });
            
            // 去重（基于文本和位置）
            const unique = [];
            const seen = new Set();
            
            results.forEach(item => {
                const key = `${item.text}_${item.x}_${item.y}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    unique.push(item);
                }
            });
            
            // 按相关性得分排序
            return unique.sort((a, b) => b.relevanceScore - a.relevanceScore);
        }
    """)
    
    print(f"找到 {len(sources)} 个潜在的参考来源")
    
    # 显示前10个最相关的来源
    print("\n前10个最相关的来源:")
    for i, source in enumerate(sources[:10]):
        print(f"{i+1}. [{source['relevanceScore']}分] {source['text'][:50]}...")
        print(f"   位置: ({source['x']}, {source['y']}) | 可点击: {'✅' if source['isClickable'] else '❌'}")
    
    return sources

async def click_source_safely(page, context, source, source_index):
    """安全地点击参考来源"""
    try:
        print(f"\n点击来源 {source_index}: {source['text'][:60]}...")
        
        # 记录初始状态
        initial_pages = len(context.pages)
        initial_url = page.url
        
        # 尝试多种点击方法
        click_methods = [
            ("坐标点击", lambda: page.mouse.click(
                source['x'] + source['width']/2, 
                source['y'] + source['height']/2
            )),
            ("JavaScript点击", lambda: page.evaluate(f"""
                () => {{
                    const elements = Array.from(document.querySelectorAll('*'));
                    const target = elements.find(el => {{
                        const rect = el.getBoundingClientRect();
                        return Math.abs(rect.x - {source['x']}) < 15 && 
                               Math.abs(rect.y - {source['y']}) < 15 &&
                               el.innerText && el.innerText.includes("{source['text'][:20].replace('"', '')}");
                    }});
                    if (target) {{
                        target.click();
                        return true;
                    }}
                    return false;
                }}
            """)),
            ("强制点击", lambda: page.evaluate(f"""
                () => {{
                    const element = document.elementFromPoint({source['x'] + source['width']/2}, {source['y'] + source['height']/2});
                    if (element) {{
                        element.click();
                        return true;
                    }}
                    return false;
                }}
            """))
        ]
        
        click_success = False
        used_method = ""
        
        for method_name, method_func in click_methods:
            try:
                await method_func()
                await page.wait_for_timeout(3000)
                
                # 检查是否有变化
                if len(context.pages) > initial_pages or page.url != initial_url:
                    click_success = True
                    used_method = method_name
                    print(f"  ✅ {method_name}成功")
                    break
                else:
                    print(f"  ❌ {method_name}无响应")
            except Exception as e:
                print(f"  ❌ {method_name}失败: {e}")
        
        if not click_success:
            return {
                "source_index": source_index,
                "source_text": source['text'],
                "click_success": False,
                "result_type": "no_response",
                "method_used": "none",
                "article_data": {}
            }
        
        # 处理点击成功的情况
        result = {
            "source_index": source_index,
            "source_text": source['text'],
            "click_success": True,
            "method_used": used_method,
            "article_data": {}
        }
        
        if len(context.pages) > initial_pages:
            # 新标签页打开
            new_page = context.pages[-1]
            try:
                await new_page.wait_for_load_state('networkidle', timeout=15000)
                article_data = await extract_page_summary(new_page)
                result["result_type"] = "new_tab"
                result["article_data"] = article_data
                print(f"  📄 新标签页: {article_data['title'][:50]}...")
                print(f"  🔗 URL: {article_data['url']}")
                await new_page.close()
            except Exception as e:
                print(f"  ❌ 处理新标签页失败: {e}")
                await new_page.close()
        
        elif page.url != initial_url:
            # 当前页面跳转
            try:
                await page.wait_for_load_state('networkidle', timeout=15000)
                article_data = await extract_page_summary(page)
                result["result_type"] = "page_navigation"
                result["article_data"] = article_data
                print(f"  📄 页面跳转: {article_data['title'][:50]}...")
                print(f"  🔗 URL: {article_data['url']}")
                await page.go_back()
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"  ❌ 处理页面跳转失败: {e}")
                try:
                    await page.go_back()
                    await page.wait_for_timeout(3000)
                except:
                    pass
        
        return result
        
    except Exception as e:
        print(f"  ❌ 点击过程出错: {e}")
        return {
            "source_index": source_index,
            "source_text": source['text'],
            "click_success": False,
            "result_type": "error",
            "error": str(e),
            "article_data": {}
        }

async def main():
    """主函数"""
    print("🎯 增强版参考来源提取器")
    print("系统性滚动和点击右侧参考区域的所有来源")
    print("="*80)
    
    playwright = None
    context = None
    
    try:
        # 启动浏览器
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir="./deepseek_user_data",
            headless=False,
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("脚本已准备就绪，等待执行...")
        return {"status": "ready"}
        
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