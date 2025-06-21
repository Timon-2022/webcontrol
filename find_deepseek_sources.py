#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
在DeepSeek界面中查找"查看来源"、"参考资料"等按钮
尝试获取具体的网页来源链接
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def find_sources():
    """查找DeepSeek的来源信息"""
    print("=" * 70)
    print("�� DeepSeek 来源信息查找 - 寻找来源按钮")
    print("=" * 70)
    
    # 加载登录状态
    login_files = ["deepseek_login_state.json", "login_state.json"]
    login_state = None
    
    for file in login_files:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                login_state = json.load(f)
            print(f"✅ 加载登录状态: {file}")
            break
    
    if not login_state:
        print("⚠️ 未找到登录状态文件")
        return
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=300,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(storage_state=login_state)
            page = await context.new_page()
            
            print("🌐 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            await page.wait_for_timeout(3000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 点击联网搜索
            print("🔍 启用联网搜索...")
            web_search_btn = await page.wait_for_selector("text=联网搜索", timeout=10000)
            await web_search_btn.click()
            await page.wait_for_timeout(2000)
            
            # 输入搜索
            print("⌨️ 输入搜索内容...")
            input_box = await page.wait_for_selector("textarea", timeout=10000)
            query = "小鸡科技的详细信息，包括公司背景、主要业务、发展历程、最新动态"
            await input_box.fill(query)
            await page.wait_for_timeout(1000)
            await input_box.press('Enter')
            
            print("⏳ 等待搜索完成...")
            await page.wait_for_timeout(15000)
            
            # 查找所有可能的来源相关按钮和链接
            print("🔍 查找来源相关的按钮和链接...")
            
            source_button_selectors = [
                # 中文按钮
                "text=查看来源",
                "text=参考资料",
                "text=来源",
                "text=引用",
                "text=参考",
                "text=资料来源",
                "text=网页来源",
                "text=搜索来源",
                
                # 英文按钮
                "text=View Sources",
                "text=Sources",
                "text=References",
                "text=Citations",
                "text=Web Sources",
                
                # 按钮选择器
                "button:has-text('来源')",
                "button:has-text('参考')",
                "button:has-text('引用')",
                "button:has-text('Sources')",
                
                # 可能的图标按钮
                "[title*='来源']",
                "[title*='参考']",
                "[title*='引用']",
                "[title*='source']",
                "[aria-label*='来源']",
                "[aria-label*='参考']",
                "[aria-label*='source']",
                
                # CSS类名
                ".sources-button",
                ".references-button",
                ".citations-button",
                ".web-sources",
                ".source-link"
            ]
            
            found_source_buttons = []
            
            for selector in source_button_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"🔍 选择器 '{selector}' 找到 {len(elements)} 个元素")
                        
                        for i, element in enumerate(elements):
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            text = await element.text_content() or ""
                            title = await element.get_attribute("title") or ""
                            
                            if is_visible and text.strip():
                                found_source_buttons.append({
                                    'selector': selector,
                                    'index': i,
                                    'text': text.strip(),
                                    'title': title,
                                    'visible': is_visible,
                                    'enabled': is_enabled
                                })
                                print(f"  找到按钮 {i}: '{text.strip()}' (可见: {is_visible}, 可用: {is_enabled})")
                                
                except Exception as e:
                    print(f"❌ 选择器 {selector} 失败: {e}")
            
            # 尝试点击找到的来源按钮
            print(f"\n🖱️ 尝试点击来源按钮（共找到 {len(found_source_buttons)} 个）...")
            
            source_results = []
            for i, btn_info in enumerate(found_source_buttons[:3]):  # 只点击前3个
                try:
                    print(f"  点击按钮: '{btn_info['text']}'...")
                    
                    # 点击前截图
                    await page.screenshot(path=f"deepseek_source_{timestamp}_before_{i}.png")
                    
                    # 重新查找元素并点击
                    element = await page.query_selector(btn_info['selector'])
                    if element and await element.is_visible():
                        await element.click()
                        await page.wait_for_timeout(3000)
                        
                        # 点击后截图
                        await page.screenshot(path=f"deepseek_source_{timestamp}_after_{i}.png")
                        
                        # 检查是否出现了新的内容
                        new_content = await page.text_content('body')
                        
                        # 查找可能出现的来源列表
                        source_list_selectors = [
                            ".source-list",
                            ".references-list",
                            ".citations-list",
                            ".web-sources-list",
                            "ul li a[href*='http']",
                            "ol li a[href*='http']",
                            "div[data-testid*='source']",
                            ".modal .source",
                            ".popup .reference"
                        ]
                        
                        found_sources = []
                        for list_selector in source_list_selectors:
                            try:
                                source_elements = await page.query_selector_all(list_selector)
                                for source_elem in source_elements:
                                    source_text = await source_elem.text_content()
                                    source_href = await source_elem.get_attribute('href')
                                    
                                    if source_text and (source_href or 'http' in source_text):
                                        found_sources.append({
                                            'text': source_text.strip(),
                                            'href': source_href,
                                            'selector': list_selector
                                        })
                                        print(f"    找到来源: {source_text[:50]}... -> {source_href}")
                            except:
                                pass
                        
                        source_results.append({
                            'button': btn_info['text'],
                            'found_sources': found_sources,
                            'click_index': i
                        })
                        
                except Exception as e:
                    print(f"    ❌ 点击失败: {e}")
            
            # 查找页面中所有的HTTP链接
            print("\n�� 查找页面中的所有HTTP链接...")
            
            all_links = await page.query_selector_all("a[href*='http']")
            http_links = []
            
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    is_visible = await link.is_visible()
                    
                    if href and is_visible and text:
                        http_links.append({
                            'url': href,
                            'text': text.strip(),
                            'visible': is_visible
                        })
                        print(f"  链接: {text[:30]}... -> {href[:50]}...")
                except:
                    pass
            
            # 分析页面HTML源码中可能的引用信息
            print("\n🔍 分析页面HTML源码...")
            
            page_html = await page.content()
            
            # 在HTML中查找可能的引用模式
            import re
            
            url_patterns = [
                r'https?://[^\s"\'<>]+',
                r'data-source="([^"]+)"',
                r'data-reference="([^"]+)"',
                r'data-citation="([^"]+)"',
                r'source:\s*"([^"]+)"',
                r'reference:\s*"([^"]+)"'
            ]
            
            html_sources = []
            for pattern in url_patterns:
                matches = re.findall(pattern, page_html)
                if matches:
                    for match in matches:
                        if 'http' in match and len(match) > 10:
                            html_sources.append({
                                'pattern': pattern,
                                'url': match,
                                'type': 'html_source'
                            })
                            print(f"  HTML来源: {match[:60]}...")
            
            # 保存所有发现的来源信息
            all_sources = {
                'query': '小鸡科技',
                'timestamp': datetime.now().isoformat(),
                'found_source_buttons': found_source_buttons,
                'source_results': source_results,
                'http_links': http_links,
                'html_sources': html_sources,
                'statistics': {
                    'total_buttons': len(found_source_buttons),
                    'total_clicked': len(source_results),
                    'total_http_links': len(http_links),
                    'total_html_sources': len(html_sources)
                }
            }
            
            # 保存结果
            filename = f"data/deepseek_sources_{timestamp}.json"
            os.makedirs("data", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_sources, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 来源信息已保存到: {filename}")
            print(f"📊 来源统计:")
            print(f"  - 来源按钮: {len(found_source_buttons)} 个")
            print(f"  - 点击结果: {len(source_results)} 个")
            print(f"  - HTTP链接: {len(http_links)} 个")
            print(f"  - HTML来源: {len(html_sources)} 个")
            
            # 最终截图
            await page.screenshot(path=f"deepseek_sources_{timestamp}_final.png", full_page=True)
            print("📸 已保存最终截图")
            
            await page.wait_for_timeout(5000)
            await browser.close()
            print("✅ 来源信息查找完成")
            
    except Exception as e:
        print(f"❌ 查找失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(find_sources())
