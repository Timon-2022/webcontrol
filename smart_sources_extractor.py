#!/usr/bin/env python3
"""
智能参考来源提取器
系统性地滚动并点击右侧参考区域的所有来源，获取完整的参考网页信息
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urlparse

async def extract_page_summary(page):
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

async def scroll_and_find_sources(page):
    """滚动并查找所有参考来源"""
    print("开始滚动页面并查找参考来源...")
    
    # 多次滚动确保加载所有内容
    for i in range(6):
        print(f"  滚动轮次 {i+1}/6")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        
        # 专门滚动右侧区域
        try:
            await page.evaluate("""
                () => {
                    const rightElements = document.querySelectorAll('*');
                    rightElements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.x > 600 && rect.width > 300 && el.scrollHeight > el.clientHeight) {
                            el.scrollTop = el.scrollHeight;
                        }
                    });
                }
            """)
        except:
            pass
    
    # 查找所有可能的参考来源
    sources = await page.evaluate("""
        () => {
            const results = [];
            const allElements = document.querySelectorAll('*');
            
            allElements.forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                
                // 重点关注右侧区域
                if (rect.x > 650 && rect.width > 80 && rect.height > 10 && rect.height < 200) {
                    const text = (el.innerText || el.textContent || '').trim();
                    
                    if (text.length > 8 && text.length < 500) {
                        // 计算相关性得分
                        let score = 0;
                        
                        // 关键词匹配
                        const keywords = ['小鸡', '盖世', 'GameSir', '科技', '网络', '公司', '游戏', '外设'];
                        keywords.forEach(keyword => {
                            if (text.includes(keyword)) score += 3;
                        });
                        
                        // 元素类型
                        if (el.tagName === 'A') score += 5;
                        if (el.tagName.match(/^H[1-6]$/)) score += 4;
                        if (el.className.includes('title')) score += 4;
                        
                        // 可点击性
                        if (el.onclick !== null) score += 3;
                        if (window.getComputedStyle(el).cursor === 'pointer') score += 3;
                        
                        // 位置加分
                        if (rect.x > 800) score += 2;
                        
                        if (score > 0) {
                            results.push({
                                index: index,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                text: text,
                                tagName: el.tagName,
                                className: el.className,
                                score: score,
                                isClickable: (
                                    el.tagName === 'A' || 
                                    el.onclick !== null ||
                                    window.getComputedStyle(el).cursor === 'pointer'
                                )
                            });
                        }
                    }
                }
            });
            
            // 去重并排序
            const unique = [];
            const seen = new Set();
            
            results.forEach(item => {
                const key = item.text + '_' + item.x + '_' + item.y;
                if (!seen.has(key)) {
                    seen.add(key);
                    unique.push(item);
                }
            });
            
            return unique.sort((a, b) => b.score - a.score);
        }
    """)
    
    print(f"找到 {len(sources)} 个潜在的参考来源")
    return sources

async def click_source(page, context, source, index):
    """安全地点击参考来源"""
    try:
        print(f"\n点击来源 {index}: {source['text'][:50]}...")
        
        initial_pages = len(context.pages)
        initial_url = page.url
        
        # 尝试点击
        try:
            await page.mouse.click(
                source['x'] + source['width']/2, 
                source['y'] + source['height']/2
            )
            await page.wait_for_timeout(4000)
        except Exception as e:
            print(f"  点击失败: {e}")
            return {
                "index": index,
                "text": source['text'],
                "success": False,
                "error": str(e)
            }
        
        # 检查结果
        if len(context.pages) > initial_pages:
            # 新标签页
            new_page = context.pages[-1]
            try:
                await new_page.wait_for_load_state('networkidle', timeout=15000)
                article_data = await extract_page_summary(new_page)
                print(f"  ✅ 新标签页: {article_data['title'][:40]}...")
                await new_page.close()
                return {
                    "index": index,
                    "text": source['text'],
                    "success": True,
                    "type": "new_tab",
                    "data": article_data
                }
            except Exception as e:
                print(f"  处理新标签页失败: {e}")
                await new_page.close()
        
        elif page.url != initial_url:
            # 页面跳转
            try:
                await page.wait_for_load_state('networkidle', timeout=15000)
                article_data = await extract_page_summary(page)
                print(f"  ✅ 页面跳转: {article_data['title'][:40]}...")
                await page.go_back()
                await page.wait_for_timeout(3000)
                return {
                    "index": index,
                    "text": source['text'],
                    "success": True,
                    "type": "navigation",
                    "data": article_data
                }
            except Exception as e:
                print(f"  处理页面跳转失败: {e}")
                try:
                    await page.go_back()
                    await page.wait_for_timeout(3000)
                except:
                    pass
        
        print("  ❌ 点击无响应")
        return {
            "index": index,
            "text": source['text'],
            "success": False,
            "error": "no_response"
        }
        
    except Exception as e:
        print(f"  ❌ 点击过程出错: {e}")
        return {
            "index": index,
            "text": source['text'],
            "success": False,
            "error": str(e)
        }

async def main():
    """主函数"""
    print("🎯 智能参考来源提取器")
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
        
        # 访问DeepSeek
        print("1. 访问DeepSeek...")
        await page.goto("https://chat.deepseek.com", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 发送查询
        print("2. 发送查询...")
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        
        # 点击联网搜索
        try:
            web_search_button = await page.wait_for_selector("text=联网搜索", timeout=10000)
            await web_search_button.click()
            print("✅ 已点击联网搜索")
            await page.wait_for_timeout(2000)
        except:
            print("⚠️ 未找到联网搜索按钮")
        
        # 输入查询
        chat_input = await page.wait_for_selector("textarea", timeout=10000)
        await chat_input.fill(query)
        await chat_input.press('Enter')
        
        # 等待回复完成
        print("3. 等待回复完成...")
        await page.wait_for_timeout(45000)
        
        # 滚动并查找参考来源
        print("4. 滚动并查找参考来源...")
        sources = await scroll_and_find_sources(page)
        
        # 保存截图
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        await page.screenshot(path=f"smart_sources_{timestamp}.png", full_page=True)
        print(f"✅ 截图已保存: smart_sources_{timestamp}.png")
        
        # 显示前10个最相关的来源
        print("\n前10个最相关的来源:")
        for i, source in enumerate(sources[:10]):
            print(f"{i+1}. [{source['score']}分] {source['text'][:60]}...")
        
        # 点击参考来源
        print(f"\n5. 开始点击前 {min(20, len(sources))} 个参考来源...")
        
        results = []
        successful = 0
        max_clicks = min(20, len(sources))
        
        for i, source in enumerate(sources[:max_clicks]):
            result = await click_source(page, context, source, i + 1)
            results.append(result)
            
            if result['success']:
                successful += 1
            
            await page.wait_for_timeout(1500)
        
        # 保存结果
        final_result = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "total_sources": len(sources),
            "attempted": max_clicks,
            "successful": successful,
            "success_rate": f"{successful/max_clicks*100:.1f}%",
            "results": results,
            "sources": sources
        }
        
        result_filename = f"smart_sources_result_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 结果已保存到: {result_filename}")
        print(f"📊 最终统计:")
        print(f"   - 找到参考来源: {len(sources)} 个")
        print(f"   - 尝试点击: {max_clicks} 个")
        print(f"   - 成功点击: {successful} 个")
        print(f"   - 成功率: {successful/max_clicks*100:.1f}%")
        
        # 显示成功访问的页面
        print(f"\n📄 成功访问的页面:")
        for result in results:
            if result['success'] and 'data' in result:
                data = result['data']
                print(f"   - {data.get('title', 'Unknown')[:50]}...")
                print(f"     URL: {data.get('url', 'Unknown')}")
                print(f"     简报: {data.get('summary', 'No summary')[:80]}...")
                print()
        
        return final_result
        
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