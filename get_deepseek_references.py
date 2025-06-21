#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取DeepSeek回复中的具体引用来源
尝试点击引用标记或查找来源信息
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def get_references():
    """获取DeepSeek的引用来源"""
    print("=" * 70)
    print("🔍 DeepSeek 引用来源获取 - 查找具体网站")
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
                slow_mo=500,
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
            await page.wait_for_timeout(20000)  # 等待20秒确保搜索完成
            
            # 保存完整页面截图
            await page.screenshot(path=f"deepseek_refs_{timestamp}_full.png", full_page=True)
            print("📸 已保存完整页面截图")
            
            # 查找引用相关的元素
            print("🔍 查找引用相关元素...")
            
            reference_selectors = [
                # 数字引用
                "sup",  # 上标
                ".reference",
                ".citation",
                ".footnote",
                "[data-testid*='reference']",
                "[data-testid*='citation']",
                
                # 可能的引用标记
                "span[title]",  # 带title的span
                "a[title]",     # 带title的链接
                "[data-tooltip]",
                
                # 数字标记
                "span:has-text('[1]')",
                "span:has-text('[2]')",
                "span:has-text('[3]')",
                
                # 其他可能的引用格式
                ".source-link",
                ".ref-link",
                ".web-ref"
            ]
            
            found_references = []
            
            for selector in reference_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"🔍 选择器 '{selector}' 找到 {len(elements)} 个元素")
                        
                        for i, element in enumerate(elements):
                            # 获取元素信息
                            text = await element.text_content() or ""
                            title = await element.get_attribute("title") or ""
                            href = await element.get_attribute("href") or ""
                            
                            if text.strip() or title or href:
                                ref_info = {
                                    'selector': selector,
                                    'index': i,
                                    'text': text.strip(),
                                    'title': title,
                                    'href': href,
                                    'is_clickable': await element.is_enabled()
                                }
                                found_references.append(ref_info)
                                
                                print(f"  引用 {i}: 文本='{text.strip()}', 标题='{title}', 链接='{href}'")
                                
                except Exception as e:
                    print(f"❌ 选择器 {selector} 失败: {e}")
            
            # 尝试查找可点击的数字
            print("\n🔍 查找可点击的数字引用...")
            
            # 查找页面中所有包含数字的小元素
            number_elements = await page.query_selector_all("span, sup, a")
            clickable_numbers = []
            
            for element in number_elements:
                try:
                    text = await element.text_content()
                    if text and text.strip().isdigit() and len(text.strip()) <= 2:
                        is_clickable = await element.is_enabled()
                        if is_clickable:
                            clickable_numbers.append({
                                'text': text.strip(),
                                'element': element,
                                'clickable': is_clickable
                            })
                            print(f"  可点击数字: '{text.strip()}'")
                except:
                    pass
            
            # 尝试点击一些引用数字
            print(f"\n🖱️ 尝试点击引用数字（共找到 {len(clickable_numbers)} 个）...")
            
            clicked_references = []
            for i, num_info in enumerate(clickable_numbers[:5]):  # 只点击前5个
                try:
                    print(f"  点击数字 '{num_info['text']}'...")
                    
                    # 点击前截图
                    await page.screenshot(path=f"deepseek_refs_{timestamp}_before_click_{i}.png")
                    
                    await num_info['element'].click()
                    await page.wait_for_timeout(2000)
                    
                    # 点击后截图
                    await page.screenshot(path=f"deepseek_refs_{timestamp}_after_click_{i}.png")
                    
                    # 检查是否出现了弹窗或新内容
                    page_text_after = await page.text_content('body')
                    
                    # 查找可能出现的引用信息
                    popup_selectors = [
                        ".popup",
                        ".modal",
                        ".tooltip",
                        ".reference-popup",
                        ".citation-popup",
                        "[role='dialog']",
                        "[role='tooltip']"
                    ]
                    
                    popup_content = ""
                    for popup_selector in popup_selectors:
                        try:
                            popup = await page.query_selector(popup_selector)
                            if popup and await popup.is_visible():
                                popup_text = await popup.text_content()
                                if popup_text:
                                    popup_content += popup_text + "\n"
                                    print(f"    发现弹窗内容: {popup_text[:100]}...")
                        except:
                            pass
                    
                    clicked_references.append({
                        'number': num_info['text'],
                        'popup_content': popup_content,
                        'click_index': i
                    })
                    
                    # 如果有弹窗，尝试关闭
                    try:
                        close_btn = await page.query_selector("button:has-text('关闭'), button:has-text('×'), .close")
                        if close_btn:
                            await close_btn.click()
                            await page.wait_for_timeout(1000)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"    ❌ 点击失败: {e}")
            
            # 查找页面底部可能的引用列表
            print("\n🔍 查找页面底部的引用列表...")
            
            # 滚动到页面底部
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # 查找底部引用
            bottom_selectors = [
                ".references",
                ".citations",
                ".sources",
                ".footnotes",
                "ol li",  # 有序列表
                "ul li",  # 无序列表
                ".reference-list",
                ".source-list"
            ]
            
            bottom_references = []
            for selector in bottom_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"🔍 底部选择器 '{selector}' 找到 {len(elements)} 个元素")
                        
                        for i, element in enumerate(elements):
                            text = await element.text_content()
                            if text and len(text.strip()) > 20 and any(keyword in text.lower() for keyword in ['http', 'www', '.com', '.cn', '来源', 'source']):
                                bottom_references.append({
                                    'selector': selector,
                                    'index': i,
                                    'content': text.strip()
                                })
                                print(f"  底部引用 {i}: {text[:100]}...")
                except Exception as e:
                    print(f"❌ 底部选择器 {selector} 失败: {e}")
            
            # 保存所有发现的引用信息
            all_references = {
                'query': '小鸡科技',
                'timestamp': datetime.now().isoformat(),
                'found_references': found_references,
                'clickable_numbers': [{'text': n['text'], 'clickable': n['clickable']} for n in clickable_numbers],
                'clicked_references': clicked_references,
                'bottom_references': bottom_references,
                'total_found': len(found_references),
                'total_clickable': len(clickable_numbers),
                'total_clicked': len(clicked_references),
                'total_bottom': len(bottom_references)
            }
            
            # 保存结果
            filename = f"data/deepseek_references_{timestamp}.json"
            os.makedirs("data", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_references, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 引用信息已保存到: {filename}")
            print(f"📊 引用统计:")
            print(f"  - 找到的引用元素: {len(found_references)} 个")
            print(f"  - 可点击的数字: {len(clickable_numbers)} 个")
            print(f"  - 已点击的引用: {len(clicked_references)} 个")
            print(f"  - 底部引用: {len(bottom_references)} 个")
            
            # 最终截图
            await page.screenshot(path=f"deepseek_refs_{timestamp}_final.png", full_page=True)
            print("📸 已保存最终截图")
            
            await page.wait_for_timeout(5000)
            await browser.close()
            print("✅ 引用来源获取完成")
            
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_references())
