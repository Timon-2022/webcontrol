#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek联网搜索测试 - 简化版
先点击联网搜索按钮，再搜索小鸡科技
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def test_deepseek_web_simple():
    """DeepSeek联网搜索测试"""
    print("=" * 70)
    print("🤖 DeepSeek 联网搜索测试 - 搜索小鸡科技")
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
                slow_mo=1000,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(storage_state=login_state)
            page = await context.new_page()
            
            print("🌐 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            await page.wait_for_timeout(3000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"deepseek_web_{timestamp}_start.png")
            print("📸 已保存起始截图")
            
            # 查找联网搜索按钮
            print("🔍 查找联网搜索按钮...")
            web_search_selectors = [
                "text=联网搜索",
                "text=Web Search",
                "button:has-text('联网')",
                "button:has-text('搜索')",
                "[title*='联网']",
                "[title*='搜索']"
            ]
            
            web_search_clicked = False
            for selector in web_search_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"🔍 '{selector}' 找到 {len(elements)} 个元素")
                    
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            text = await element.text_content() or ""
                            print(f"  找到按钮: '{text.strip()}'")
                            
                            if any(word in text for word in ['联网', '搜索', 'Web', 'Search']):
                                print(f"✅ 点击联网搜索按钮: '{text.strip()}'")
                                await element.click()
                                await page.wait_for_timeout(2000)
                                web_search_clicked = True
                                break
                    
                    if web_search_clicked:
                        break
                except Exception as e:
                    print(f"  ❌ 选择器失败: {e}")
            
            if web_search_clicked:
                await page.screenshot(path=f"deepseek_web_{timestamp}_clicked.png")
                print("📸 已保存点击后截图")
            else:
                print("⚠️ 未找到联网搜索按钮，分析所有按钮...")
                buttons = await page.query_selector_all("button")
                print(f"📊 页面共有 {len(buttons)} 个按钮")
                
                for i, btn in enumerate(buttons[:10]):
                    try:
                        text = await btn.text_content() or ""
                        if text.strip() and await btn.is_visible():
                            print(f"  按钮 {i}: '{text.strip()}'")
                    except:
                        pass
            
            # 查找输入框
            print("🔍 查找输入框...")
            input_element = None
            selectors = ["textarea", "[contenteditable='true']"]
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible() and await element.is_enabled():
                        input_element = element
                        print(f"✅ 找到输入框: {selector}")
                        break
                if input_element:
                    break
            
            if input_element:
                query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
                print(f"⌨️ 输入: {query}")
                
                await input_element.fill(query)
                await page.wait_for_timeout(1000)
                
                await page.screenshot(path=f"deepseek_web_{timestamp}_input.png")
                print("📸 已保存输入截图")
                
                print("📤 发送搜索...")
                await input_element.press('Enter')
                
                # 等待回复
                print("⏳ 等待回复...")
                for wait_time in [5, 10, 15, 20]:
                    await page.wait_for_timeout(5000)
                    print(f"  ⏰ 已等待 {wait_time} 秒")
                    
                    await page.screenshot(path=f"deepseek_web_{timestamp}_wait_{wait_time}s.png")
                    
                    page_text = await page.text_content('body')
                    if page_text and '小鸡科技' in page_text:
                        print(f"  ✅ 在 {wait_time}秒 检测到回复!")
                        
                        lines = []
                        for line in page_text.split('\n'):
                            line = line.strip()
                            if '小鸡科技' in line and len(line) > 10:
                                lines.append(line)
                        
                        print(f"  📄 找到 {len(lines)} 行相关内容:")
                        for i, line in enumerate(lines[:3]):
                            print(f"    {i+1}. {line[:100]}...")
                        break
                
                # 保存最终结果
                await page.screenshot(path=f"deepseek_web_{timestamp}_final.png")
                print("📸 已保存最终截图")
                
                # 保存结果到文件
                final_text = await page.text_content('body')
                if final_text and '小鸡科技' in final_text:
                    results = []
                    for line in final_text.split('\n'):
                        line = line.strip()
                        if '小鸡科技' in line and len(line) > 10:
                            results.append(line)
                    
                    if results:
                        filename = f"data/deepseek_web_{timestamp}.json"
                        os.makedirs("data", exist_ok=True)
                        
                        data = {
                            'query': '小鸡科技',
                            'timestamp': datetime.now().isoformat(),
                            'web_search_used': web_search_clicked,
                            'total_results': len(results),
                            'results': results
                        }
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        print(f"💾 结果已保存: {filename}")
                        print(f"📊 共 {len(results)} 条结果")
            
            await page.wait_for_timeout(10000)
            await browser.close()
            print("✅ 测试完成")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_deepseek_web_simple())
