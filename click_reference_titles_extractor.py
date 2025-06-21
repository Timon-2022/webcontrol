#!/usr/bin/env python3
"""
点击参考来源标题提取器
专门模拟人工点击右侧参考来源标题的行为，获取原文章的完整地址和内容
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    """主函数"""
    print("🎯 点击参考来源标题提取器")
    print("模拟人工点击右侧参考来源标题，获取原文章地址")
    print("="*80)
    
    playwright = None
    page = None
    
    try:
        # 1. 启动浏览器
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir="./deepseek_user_data",
            headless=False
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
        chat_input = await page.wait_for_selector("textarea", timeout=10000)
        await chat_input.fill(query)
        await chat_input.press('Enter')
        
        # 4. 等待回复完成
        print("4. 等待回复完成...")
        await page.wait_for_timeout(40000)
        
        # 5. 查找并点击源链接
        print("5. 查找并点击源链接...")
        sources_element = None
        selectors = ["text=已搜索到", "[class*='source']", "text=/已搜索到\\\\d+个网页/"]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if '搜索到' in text and ('网页' in text or '个' in text):
                        sources_element = element
                        print(f"✅ 找到源信息: {text}")
                        break
                if sources_element:
                    break
            except:
                continue
        
        if sources_element:
            print("6. 点击源链接...")
            await sources_element.click()
            await page.wait_for_timeout(10000)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=f"click_titles_{timestamp}.png")
            print(f"✅ 截图已保存: click_titles_{timestamp}.png")
        
        # 7. 查找右侧区域的所有可点击标题
        print("7. 查找右侧区域的可点击标题...")
        
        # 使用更精确的方法查找可点击的标题元素
        clickable_titles = await page.evaluate("""
            () => {
                const results = [];
                const rightAreaElements = document.querySelectorAll('*');
                
                rightAreaElements.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    
                    // 只考虑右侧区域的元素 (x > 800)
                    if (rect.x > 800 && rect.width > 100 && rect.height > 20) {
                        const text = el.innerText || el.textContent || '';
                        
                        // 查找看起来像标题的元素
                        const isTitle = (
                            // 包含公司名称相关关键词
                            (text.includes('小鸡') || text.includes('盖世') || text.includes('GameSir') || 
                             text.includes('科技') || text.includes('网络') || text.includes('公司')) &&
                            // 文本长度适中（标题通常不会太长也不会太短）
                            text.length > 10 && text.length < 200 &&
                            // 不是纯数字或日期
                            !/^\\d+$/.test(text.trim()) &&
                            !/^\\d{4}\\/\\d{1,2}\\/\\d{1,2}$/.test(text.trim())
                        );
                        
                        // 检查是否可点击
                        const isClickable = (
                            el.tagName === 'A' ||
                            el.onclick !== null ||
                            el.getAttribute('role') === 'button' ||
                            el.style.cursor === 'pointer' ||
                            window.getComputedStyle(el).cursor === 'pointer' ||
                            el.querySelector('a') !== null
                        );
                        
                        // 检查是否有点击事件监听器
                        const hasClickListener = el.onclick !== null;
                        
                        if (isTitle || isClickable || text.length > 50) {
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
                                isTitle: isTitle,
                                isClickable: isClickable,
                                hasClickListener: hasClickListener,
                                hasLink: el.querySelector('a') !== null,
                                href: el.href || (el.querySelector('a') && el.querySelector('a').href) || null,
                                cursor: window.getComputedStyle(el).cursor
                            });
                        }
                    }
                });
                
                // 按照标题可能性和可点击性排序
                return results.sort((a, b) => {
                    const scoreA = (a.isTitle ? 10 : 0) + (a.isClickable ? 5 : 0) + (a.hasLink ? 3 : 0);
                    const scoreB = (b.isTitle ? 10 : 0) + (b.isClickable ? 5 : 0) + (b.hasLink ? 3 : 0);
                    return scoreB - scoreA;
                });
            }
        """)
        
        print(f"找到 {len(clickable_titles)} 个可能的可点击标题")
        
        # 8. 显示找到的标题信息
        print("\\n8. 分析找到的标题:")
        for i, title in enumerate(clickable_titles[:15]):  # 只显示前15个
            print(f"\\n标题 {i+1}:")
            print(f"  文本: {title['text'][:80]}...")
            print(f"  标签: {title['tagName']}")
            print(f"  位置: ({title['x']:.0f}, {title['y']:.0f})")
            print(f"  是否标题: {'✅' if title['isTitle'] else '❌'}")
            print(f"  是否可点击: {'✅' if title['isClickable'] else '❌'}")
            print(f"  包含链接: {'✅' if title['hasLink'] else '❌'}")
            print(f"  鼠标样式: {title['cursor']}")
            if title['href']:
                print(f"  链接地址: {title['href']}")
        
        # 9. 依次点击最有希望的标题
        print(f"\\n9. 依次点击前 {min(10, len(clickable_titles))} 个最有希望的标题...")
        
        extracted_articles = []
        titles_to_click = clickable_titles[:10]  # 只点击前10个
        
        for i, title_info in enumerate(titles_to_click):
            try:
                print(f"\\n点击标题 {i+1}/{len(titles_to_click)}: {title_info['text'][:50]}...")
                
                # 记录点击前的状态
                before_url = page.url
                before_page_count = len(context.pages)
                
                # 尝试点击元素
                try:
                    # 方法1: 通过坐标点击
                    await page.mouse.click(title_info['x'] + title_info['width']/2, 
                                         title_info['y'] + title_info['height']/2)
                    await page.wait_for_timeout(3000)
                    
                except Exception as e1:
                    print(f"  坐标点击失败: {e1}")
                    try:
                        # 方法2: 通过JavaScript点击
                        text_safe = title_info['text'][:20].replace('"', '\\"')
                        await page.evaluate(f"""
                            () => {{
                                const elements = document.querySelectorAll('*');
                                for (let el of elements) {{
                                    const rect = el.getBoundingClientRect();
                                    if (Math.abs(rect.x - {title_info['x']}) < 5 && 
                                        Math.abs(rect.y - {title_info['y']}) < 5 &&
                                        el.innerText.includes("{text_safe}")) {{
                                        el.click();
                                        break;
                                    }}
                                }}
                            }}
                        """)
                        await page.wait_for_timeout(3000)
                    except Exception as e2:
                        print(f"  JavaScript点击也失败: {e2}")
                        continue
                
                # 检查点击结果
                after_page_count = len(context.pages)
                after_url = page.url
                
                click_result = {
                    'title_index': i + 1,
                    'title_text': title_info['text'][:200],
                    'click_success': False,
                    'result_type': '',
                    'article_data': {}
                }
                
                if after_page_count > before_page_count:
                    # 新窗口打开
                    print(f"  ✅ 打开了新窗口")
                    new_page = context.pages[-1]
                    
                    try:
                        await new_page.wait_for_load_state('load', timeout=15000)
                        
                        # 提取文章信息
                        article_info = await new_page.evaluate("""
                            () => {
                                return {
                                    url: window.location.href,
                                    title: document.title || '',
                                    description: (document.querySelector('meta[name="description"]') || {}).content || '',
                                    keywords: (document.querySelector('meta[name="keywords"]') || {}).content || '',
                                    author: (document.querySelector('meta[name="author"]') || {}).content || '',
                                    publish_date: (document.querySelector('meta[property="article:published_time"]') || 
                                                  document.querySelector('meta[name="publish_date"]') || {}).content || '',
                                    h1_texts: Array.from(document.querySelectorAll('h1')).map(h => h.innerText).slice(0, 3),
                                    h2_texts: Array.from(document.querySelectorAll('h2')).map(h => h.innerText).slice(0, 5),
                                    article_content: (document.querySelector('article') || 
                                                    document.querySelector('.content') || 
                                                    document.querySelector('.article-content') ||
                                                    document.querySelector('main') ||
                                                    document.body).innerText.substring(0, 2000),
                                    links_count: document.querySelectorAll('a[href]').length,
                                    images_count: document.querySelectorAll('img').length,
                                    domain: window.location.hostname
                                };
                            }
                        """)
                        
                        click_result['click_success'] = True
                        click_result['result_type'] = 'new_window'
                        click_result['article_data'] = article_info
                        
                        print(f"    📄 文章标题: {article_info['title'][:60]}...")
                        print(f"    🔗 文章URL: {article_info['url']}")
                        print(f"    🏢 域名: {article_info['domain']}")
                        
                        # 保存单独的文章截图
                        await new_page.screenshot(path=f"article_{i+1}_{timestamp}.png")
                        print(f"    📸 文章截图: article_{i+1}_{timestamp}.png")
                        
                    except Exception as e:
                        print(f"    ❌ 提取文章信息失败: {e}")
                        click_result['article_data'] = {'error': str(e)}
                    
                    finally:
                        await new_page.close()
                        
                elif after_url != before_url:
                    # 当前页面跳转
                    print(f"  ✅ 页面跳转到: {after_url}")
                    
                    try:
                        await page.wait_for_load_state('load', timeout=15000)
                        
                        # 提取文章信息
                        article_info = await page.evaluate("""
                            () => {
                                return {
                                    url: window.location.href,
                                    title: document.title || '',
                                    description: (document.querySelector('meta[name="description"]') || {}).content || '',
                                    keywords: (document.querySelector('meta[name="keywords"]') || {}).content || '',
                                    author: (document.querySelector('meta[name="author"]') || {}).content || '',
                                    publish_date: (document.querySelector('meta[property="article:published_time"]') || 
                                                  document.querySelector('meta[name="publish_date"]') || {}).content || '',
                                    h1_texts: Array.from(document.querySelectorAll('h1')).map(h => h.innerText).slice(0, 3),
                                    h2_texts: Array.from(document.querySelectorAll('h2')).map(h => h.innerText).slice(0, 5),
                                    article_content: (document.querySelector('article') || 
                                                    document.querySelector('.content') || 
                                                    document.querySelector('.article-content') ||
                                                    document.querySelector('main') ||
                                                    document.body).innerText.substring(0, 2000),
                                    links_count: document.querySelectorAll('a[href]').length,
                                    images_count: document.querySelectorAll('img').length,
                                    domain: window.location.hostname
                                };
                            }
                        """)
                        
                        click_result['click_success'] = True
                        click_result['result_type'] = 'page_navigation'
                        click_result['article_data'] = article_info
                        
                        print(f"    📄 文章标题: {article_info['title'][:60]}...")
                        print(f"    🔗 文章URL: {article_info['url']}")
                        
                        # 保存文章截图
                        await page.screenshot(path=f"article_{i+1}_{timestamp}.png")
                        print(f"    📸 文章截图: article_{i+1}_{timestamp}.png")
                        
                        # 返回原页面
                        await page.go_back()
                        await page.wait_for_timeout(3000)
                        
                    except Exception as e:
                        print(f"    ❌ 提取文章信息失败: {e}")
                        click_result['article_data'] = {'error': str(e)}
                        
                        # 尝试返回原页面
                        try:
                            await page.go_back()
                            await page.wait_for_timeout(3000)
                        except:
                            pass
                else:
                    print(f"  ❌ 点击后没有明显变化")
                
                extracted_articles.append(click_result)
                
                # 每次点击后等待一下
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"  ❌ 点击标题 {i+1} 时出错: {e}")
                extracted_articles.append({
                    'title_index': i + 1,
                    'title_text': title_info['text'][:200],
                    'click_success': False,
                    'error': str(e)
                })
        
        # 10. 保存结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'total_titles_found': len(clickable_titles),
            'titles_attempted': len(titles_to_click),
            'successful_clicks': len([a for a in extracted_articles if a.get('click_success', False)]),
            'extracted_articles': extracted_articles,
            'all_titles_info': clickable_titles
        }
        
        result_filename = f"click_titles_result_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\\n✅ 结果已保存: {result_filename}")
        print(f"\\n🎯 总结:")
        print(f"  - 找到标题: {result['total_titles_found']}")
        print(f"  - 尝试点击: {result['titles_attempted']}")
        print(f"  - 成功点击: {result['successful_clicks']}")
        
        if result['successful_clicks'] > 0:
            print(f"\\n📄 成功获取的文章:")
            for article in extracted_articles:
                if article.get('click_success', False):
                    data = article['article_data']
                    print(f"  ✅ {article['title_text'][:50]}...")
                    print(f"     📄 标题: {data.get('title', 'N/A')[:60]}...")
                    print(f"     🔗 URL: {data.get('url', 'N/A')}")
                    print(f"     🏢 域名: {data.get('domain', 'N/A')}")
                    if data.get('publish_date'):
                        print(f"     📅 发布日期: {data['publish_date']}")
                    print(f"     📝 内容预览: {data.get('article_content', '')[:100]}...")
                    print()
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            if page and page.context:
                await page.context.close()
            if playwright:
                await playwright.stop()
            print("✅ 浏览器已关闭")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
