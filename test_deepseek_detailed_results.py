#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek详细搜索结果提取
获取联网搜索的30个网页详细信息
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def extract_detailed_results():
    """提取DeepSeek联网搜索的详细结果"""
    print("=" * 70)
    print("🔍 DeepSeek 详细搜索结果提取 - 获取30个网页信息")
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
                slow_mo=800,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(storage_state=login_state)
            page = await context.new_page()
            
            print("🌐 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            await page.wait_for_timeout(3000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 点击联网搜索按钮
            print("🔍 点击联网搜索按钮...")
            web_search_btn = await page.wait_for_selector("text=联网搜索", timeout=10000)
            if web_search_btn:
                await web_search_btn.click()
                await page.wait_for_timeout(2000)
                print("✅ 已点击联网搜索")
            
            # 输入搜索内容
            print("⌨️ 输入搜索内容...")
            input_box = await page.wait_for_selector("textarea", timeout=10000)
            query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
            await input_box.fill(query)
            await page.wait_for_timeout(1000)
            
            print("📤 发送搜索请求...")
            await input_box.press('Enter')
            
            # 等待搜索完成
            print("⏳ 等待搜索完成...")
            await page.wait_for_timeout(10000)  # 等待10秒让搜索完成
            
            # 尝试获取详细的搜索结果
            print("🔍 提取详细搜索结果...")
            
            # 方法1: 查找搜索结果链接
            print("📊 方法1: 查找搜索结果链接...")
            search_links = []
            link_selectors = [
                "a[href*='http']",
                ".search-result a",
                ".web-result a",
                "[data-testid*='link']"
            ]
            
            for selector in link_selectors:
                try:
                    links = await page.query_selector_all(selector)
                    print(f"  选择器 '{selector}' 找到 {len(links)} 个链接")
                    
                    for i, link in enumerate(links):
                        href = await link.get_attribute('href')
                        text = await link.text_content()
                        
                        if href and href.startswith('http') and text:
                            search_links.append({
                                'url': href,
                                'title': text.strip(),
                                'selector': selector,
                                'index': i
                            })
                            print(f"    链接 {i}: {text.strip()[:50]}... -> {href[:50]}...")
                except Exception as e:
                    print(f"  ❌ 选择器 {selector} 失败: {e}")
            
            # 方法2: 查找引用/来源信息
            print("\n📊 方法2: 查找引用和来源信息...")
            source_selectors = [
                ".source",
                ".reference",
                ".citation",
                "[data-testid*='source']",
                "[data-testid*='reference']",
                ".web-source"
            ]
            
            sources = []
            for selector in source_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"  选择器 '{selector}' 找到 {len(elements)} 个来源")
                    
                    for i, element in enumerate(elements):
                        text = await element.text_content()
                        if text and len(text.strip()) > 5:
                            sources.append({
                                'text': text.strip(),
                                'selector': selector,
                                'index': i
                            })
                            print(f"    来源 {i}: {text.strip()[:80]}...")
                except Exception as e:
                    print(f"  ❌ 选择器 {selector} 失败: {e}")
            
            # 方法3: 分析完整的回复内容，查找网页引用
            print("\n📊 方法3: 分析回复内容中的网页引用...")
            page_content = await page.text_content('body')
            
            # 查找可能的网页引用模式
            import re
            url_patterns = [
                r'https?://[^\s\)]+',
                r'www\.[^\s\)]+',
                r'\[[0-9]+\]',  # 引用标记
                r'来源：[^\n]+',
                r'参考：[^\n]+',
                r'引用：[^\n]+',
            ]
            
            web_references = []
            for pattern in url_patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    print(f"  模式 '{pattern}' 找到 {len(matches)} 个匹配")
                    for match in matches[:5]:  # 只显示前5个
                        web_references.append({
                            'pattern': pattern,
                            'match': match,
                            'type': 'url_reference'
                        })
                        print(f"    匹配: {match}")
            
            # 方法4: 查找具体的搜索结果块
            print("\n📊 方法4: 查找搜索结果块...")
            result_selectors = [
                ".search-results",
                ".web-results",
                ".result-item",
                "[data-testid*='result']",
                ".markdown ul li",
                ".markdown ol li"
            ]
            
            result_blocks = []
            for selector in result_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"  选择器 '{selector}' 找到 {len(elements)} 个结果块")
                    
                    for i, element in enumerate(elements):
                        text = await element.text_content()
                        if text and len(text.strip()) > 20:
                            result_blocks.append({
                                'text': text.strip(),
                                'selector': selector,
                                'index': i
                            })
                            print(f"    结果块 {i}: {text.strip()[:100]}...")
                except Exception as e:
                    print(f"  ❌ 选择器 {selector} 失败: {e}")
            
            # 保存详细结果
            detailed_results = {
                'query': '小鸡科技',
                'timestamp': datetime.now().isoformat(),
                'search_links': search_links,
                'sources': sources,
                'web_references': web_references,
                'result_blocks': result_blocks,
                'total_links': len(search_links),
                'total_sources': len(sources),
                'total_references': len(web_references),
                'total_blocks': len(result_blocks)
            }
            
            # 保存到文件
            filename = f"data/deepseek_detailed_results_{timestamp}.json"
            os.makedirs("data", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(detailed_results, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 详细结果已保存到: {filename}")
            print(f"📊 统计信息:")
            print(f"  - 搜索链接: {len(search_links)} 个")
            print(f"  - 来源信息: {len(sources)} 个")
            print(f"  - 网页引用: {len(web_references)} 个")
            print(f"  - 结果块: {len(result_blocks)} 个")
            
            # 保存最终截图
            await page.screenshot(path=f"deepseek_detailed_{timestamp}.png", full_page=True)
            print(f"📸 已保存完整页面截图: deepseek_detailed_{timestamp}.png")
            
            # 尝试点击展开更多结果
            print("\n🔍 尝试查找'查看更多'或'展开'按钮...")
            expand_selectors = [
                "text=查看更多",
                "text=展开",
                "text=更多结果",
                "text=Show more",
                "button:has-text('更多')",
                ".expand-button",
                "[data-testid*='expand']"
            ]
            
            for selector in expand_selectors:
                try:
                    expand_btn = await page.query_selector(selector)
                    if expand_btn and await expand_btn.is_visible():
                        print(f"✅ 找到展开按钮: {selector}")
                        await expand_btn.click()
                        await page.wait_for_timeout(3000)
                        
                        # 重新截图
                        await page.screenshot(path=f"deepseek_expanded_{timestamp}.png", full_page=True)
                        print("📸 已保存展开后截图")
                        break
                except:
                    pass
            
            await page.wait_for_timeout(5000)
            await browser.close()
            print("✅ 详细结果提取完成")
            
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(extract_detailed_results())
