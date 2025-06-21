#!/usr/bin/env python3
"""
右侧参考来源提取器
专门针对右侧参考来源区域，依次点击所有数据来源并保存网站信息
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    """主函数"""
    print("🎯 右侧参考来源提取器")
    print("专门针对右侧参考来源区域，依次点击所有数据来源")
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
        selectors = ["text=已搜索到", "[class*='source']", "text=/已搜索到\\d+个网页/"]
        
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
            await page.screenshot(path=f"right_panel_{timestamp}.png")
            print(f"✅ 截图已保存: right_panel_{timestamp}.png")
        
        # 7. 查找右侧区域的所有可能元素
        print("7. 查找右侧区域的所有元素...")
        
        # 获取页面尺寸
        viewport = page.viewport_size
        page_width = viewport['width']
        
        print(f"页面宽度: {page_width}px")
        
        # 查找右侧区域的元素（x坐标大于页面宽度的60%）
        right_area_threshold = page_width * 0.6
        
        right_elements = await page.evaluate(f"""
            (threshold) => {{
                const elements = [];
                const allElements = document.querySelectorAll('*');
                
                allElements.forEach((el, index) => {{
                    const rect = el.getBoundingClientRect();
                    
                    // 只考虑右侧区域的元素
                    if (rect.x > threshold && rect.width > 50 && rect.height > 20) {{
                        const clickables = el.querySelectorAll('a, button, [role="button"], [onclick]');
                        
                        if (clickables.length > 0 || el.innerText.length > 20) {{
                            elements.push({{
                                index: index,
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id,
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                text: el.innerText.substring(0, 200),
                                clickableCount: clickables.length,
                                hasHref: el.href ? true : false,
                                href: el.href || null
                            }});
                        }}
                    }}
                }});
                
                return elements;
            }}
        """, right_area_threshold)
        
        print(f"右侧区域找到 {len(right_elements)} 个可能的元素")
        
        # 8. 分析右侧元素
        clickable_sources = []
        
        for i, elem_info in enumerate(right_elements):
            print(f"\\n元素 {i+1}:")
            print(f"  标签: {elem_info['tagName']}")
            print(f"  位置: ({elem_info['x']:.0f}, {elem_info['y']:.0f})")
            print(f"  大小: {elem_info['width']:.0f} x {elem_info['height']:.0f}")
            print(f"  可点击元素数: {elem_info['clickableCount']}")
            print(f"  文本预览: {elem_info['text'][:100]}...")
            
            if elem_info['hasHref']:
                print(f"  链接: {elem_info['href']}")
            
            # 如果元素包含可点击内容，添加到候选列表
            if elem_info['clickableCount'] > 0 or elem_info['hasHref']:
                clickable_sources.append(elem_info)
        
        print(f"\\n找到 {len(clickable_sources)} 个可能的可点击源")
        
        # 9. 尝试点击右侧区域的元素
        extracted_data = []
        
        if clickable_sources:
            print(f"\\n9. 尝试点击右侧区域的前 {min(5, len(clickable_sources))} 个元素...")
            
            for i, source in enumerate(clickable_sources[:5]):  # 只尝试前5个
                try:
                    print(f"\\n尝试点击元素 {i+1}: {source['text'][:50]}...")
                    
                    # 记录点击前的状态
                    before_url = page.url
                    before_page_count = len(context.pages)
                    
                    # 尝试点击
                    await page.evaluate(f"""
                        () => {{
                            const allElements = document.querySelectorAll('*');
                            for (let el of allElements) {{
                                const rect = el.getBoundingClientRect();
                                if (Math.abs(rect.x - {source['x']}) < 5 && 
                                    Math.abs(rect.y - {source['y']}) < 5) {{
                                    el.click();
                                    break;
                                }}
                            }}
                        }}
                    """)
                    
                    # 等待变化
                    await page.wait_for_timeout(3000)
                    
                    # 检查结果
                    after_page_count = len(context.pages)
                    after_url = page.url
                    
                    click_result = {
                        'source_index': i + 1,
                        'source_text': source['text'][:100],
                        'click_success': False,
                        'result_type': '',
                        'data': {}
                    }
                    
                    if after_page_count > before_page_count:
                        # 新窗口打开
                        print(f"  ✅ 打开了新窗口")
                        new_page = context.pages[-1]
                        await new_page.wait_for_load_state('load', timeout=10000)
                        
                        click_result['click_success'] = True
                        click_result['result_type'] = 'new_window'
                        click_result['data'] = {
                            'url': new_page.url,
                            'title': await new_page.title(),
                            'content_preview': (await new_page.evaluate("document.body ? document.body.innerText : ''"))[:500]
                        }
                        
                        print(f"    URL: {new_page.url}")
                        print(f"    标题: {click_result['data']['title']}")
                        
                        await new_page.close()
                        
                    elif after_url != before_url:
                        # 当前页面跳转
                        print(f"  ✅ 页面跳转到: {after_url}")
                        await page.wait_for_load_state('load', timeout=10000)
                        
                        click_result['click_success'] = True
                        click_result['result_type'] = 'page_navigation'
                        click_result['data'] = {
                            'url': after_url,
                            'title': await page.title(),
                            'content_preview': (await page.evaluate("document.body ? document.body.innerText : ''"))[:500]
                        }
                        
                        # 返回原页面
                        await page.go_back()
                        await page.wait_for_timeout(3000)
                        
                    else:
                        print(f"  ❌ 点击后没有明显变化")
                    
                    extracted_data.append(click_result)
                    
                except Exception as e:
                    print(f"  ❌ 点击元素 {i+1} 时出错: {e}")
                    extracted_data.append({
                        'source_index': i + 1,
                        'source_text': source['text'][:100],
                        'click_success': False,
                        'error': str(e)
                    })
        
        # 10. 保存结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'right_elements_found': len(right_elements),
            'clickable_sources_found': len(clickable_sources),
            'sources_attempted': len(extracted_data),
            'successful_clicks': len([d for d in extracted_data if d.get('click_success', False)]),
            'extracted_data': extracted_data
        }
        
        result_filename = f"right_panel_sources_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\\n✅ 结果已保存: {result_filename}")
        print(f"\\n🎯 总结:")
        print(f"  - 右侧区域元素: {result['right_elements_found']}")
        print(f"  - 可点击源: {result['clickable_sources_found']}")
        print(f"  - 尝试点击: {result['sources_attempted']}")
        print(f"  - 成功点击: {result['successful_clicks']}")
        
        if result['successful_clicks'] > 0:
            print(f"\\n📄 成功提取的数据:")
            for data in extracted_data:
                if data.get('click_success', False):
                    print(f"  ✅ {data['source_text'][:50]}...")
                    print(f"     类型: {data['result_type']}")
                    if data['result_type'] in ['new_window', 'page_navigation']:
                        print(f"     URL: {data['data']['url']}")
                        print(f"     标题: {data['data']['title']}")
        
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
