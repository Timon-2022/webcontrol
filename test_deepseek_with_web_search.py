#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek联网搜索测试 - 先点击联网搜索按钮
搜索小鸡科技
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def test_deepseek_web_search():
    """DeepSeek联网搜索测试"""
    print("=" * 70)
    print("🤖 DeepSeek 联网搜索测试 - 搜索小鸡科技")
    print("=" * 70)
    
    # 检查登录状态文件
    login_files = ["deepseek_login_state.json", "login_state.json"]
    login_state = None
    
    for file in login_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    login_state = json.load(f)
                print(f"✅ 加载登录状态: {file}")
                break
            except Exception as e:
                print(f"❌ 加载 {file} 失败: {e}")
                continue
    
    if not login_state:
        print("⚠️ 未找到有效的登录状态文件")
        return
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1000,  # 慢动作便于观察
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            print("✅ 浏览器启动成功")
            context = await browser.new_context(storage_state=login_state)
            page = await context.new_page()
            
            print("🌐 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"deepseek_web_{timestamp}_1_start.png")
            print(f"📸 已保存起始截图")
            
            # 查找并点击联网搜索按钮
            print("\n🔍 查找联网搜索按钮...")
            web_search_selectors = [
                "text=联网搜索",
                "text=Web Search", 
                "text=网络搜索",
                "button:has-text('联网')",
                "button:has-text('搜索')",
                "[data-testid*='web']",
                "[data-testid*='search']",
                ".web-search",
                ".search-button",
                "button[title*='联网']",
                "button[title*='搜索']"
            ]
            
            web_search_button = None
            for selector in web_search_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"🔍 选择器 '{selector}' 找到 {len(elements)} 个元素")
                    
                    for i, element in enumerate(elements):
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            # 获取元素文本确认
                            text = await element.text_content()
                            print(f"  元素 {i}: 文本='{text}', 可见={is_visible}, 可用={is_enabled}")
                            
                            if text and any(keyword in text.lower() for keyword in ['联网', '搜索', 'web', 'search']):
                                web_search_button = element
                                print(f"✅ 找到联网搜索按钮: {selector} - '{text}'")
                                break
                    
                    if web_search_button:
                        break
                except Exception as e:
                    print(f"  ❌ 选择器 {selector} 失败: {e}")
                    continue
            
            if web_search_button:
                print("🔘 点击联网搜索按钮...")
                await web_search_button.click()
                await page.wait_for_timeout(2000)
                
                await page.screenshot(path=f"deepseek_web_{timestamp}_2_after_click.png")
                print("📸 已保存点击后截图")
            else:
                print("⚠️ 未找到联网搜索按钮，尝试直接搜索...")
                
                # 尝试查找页面上所有按钮，帮助调试
                print("\n🔍 分析页面上的所有按钮...")
                try:
                    all_buttons = await page.query_selector_all("button")
                    print(f"📊 页面共有 {len(all_buttons)} 个按钮")
                    
                    for i, button in enumerate(all_buttons[:10]):  # 只显示前10个
                        try:
                            text = await button.text_content()
                            is_visible = await button.is_visible()
                            if text and is_visible:
                                print(f"  按钮 {i}: '{text.strip()}'")
                        except:
                            pass
                except Exception as e:
                    print(f"❌ 分析按钮失败: {e}")
            
            # 查找输入框
            print("\n🔍 查找输入框...")
            input_element = None
            selectors = [
                "textarea[placeholder*='输入']",
                "textarea[placeholder*='问我']",
                "textarea",
                "[contenteditable='true']"
            ]
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                print(f"🔍 选择器 '{selector}' 找到 {len(elements)} 个元素")
                
                for i, element in enumerate(elements):
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        input_element = element
                        print(f"✅ 找到输入框: {selector} (元素 {i})")
                        break
                
                if input_element:
                    break
            
            if input_element:
                query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
                print(f"⌨️ 输入搜索内容: {query}")
                
                # 清空并输入内容
                await input_element.fill("")
                await page.wait_for_timeout(500)
                await input_element.fill(query)
                await page.wait_for_timeout(1000)
                
                await page.screenshot(path=f"deepseek_web_{timestamp}_3_input.png")
                print("📸 已保存输入后截图")
                
                # 发送消息
                print("📤 发送搜索请求...")
                await input_element.press('Enter')
                
                # 等待回复，分阶段检查
                print("⏳ 等待DeepSeek联网搜索回复...")
                
                for wait_time in [5, 10, 15, 20, 30]:
                    await page.wait_for_timeout(5000)
                    print(f"  ⏰ 已等待 {wait_time} 秒...")
                    
                    # 保存当前状态截图
                    await page.screenshot(path=f"deepseek_web_{timestamp}_4_wait_{wait_time}s.png")
                    print(f"  📸 已保存 {wait_time}秒 等待截图")
                    
                    # 检查页面内容
                    try:
                        page_text = await page.text_content('body')
                                                 if page_text and '小鸡科技' in page_text:
                             print(f"  ✅ 在 {wait_time}秒 时检测到回复内容!")
                             
                             # 查找包含关键词的具体内容
                             lines = [line.strip() for line in page_text.split('\n') 
                                   if '小鸡科技' in line and len(line.strip()) > 10]
                            
                            if lines:
                                print(f"  📄 找到 {len(lines)} 行相关内容:")
                                for i, line in enumerate(lines[:5]):  # 显示前5行
                                    print(f"    {i+1}. {line[:150]}...")
                            break
                    except:
                        pass
                
                # 最终结果截图
                await page.screenshot(path=f"deepseek_web_{timestamp}_5_final.png")
                print("📸 已保存最终结果截图")
                
                # 尝试保存结果到文件
                try:
                    final_page_text = await page.text_content('body')
                    if final_page_text and '小鸡科技' in final_page_text:
                        # 提取相关内容
                        relevant_content = []
                        lines = final_page_text.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            if '小鸡科技' in line and len(line) > 10:
                                relevant_content.append(line)
                        
                        if relevant_content:
                            # 保存到JSON文件
                            filename = f"data/deepseek_web_search_{timestamp}.json"
                            os.makedirs("data", exist_ok=True)
                            
                            result = {
                                'query': '小鸡科技',
                                'timestamp': datetime.now().isoformat(),
                                'page_title': title,
                                'used_web_search': web_search_button is not None,
                                'total_results': len(relevant_content),
                                'results': relevant_content,
                                'test_type': 'web_search_test'
                            }
                            
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(result, f, ensure_ascii=False, indent=2)
                            
                            print(f"💾 搜索结果已保存到: {filename}")
                            print(f"📊 共找到 {len(relevant_content)} 条相关内容")
                        else:
                            print("❌ 未找到包含'小鸡科技'的具体内容")
                    else:
                        print("❌ 页面中未找到'小鸡科技'相关信息")
                except Exception as e:
                    print(f"❌ 保存结果失败: {e}")
                
            else:
                print("❌ 未找到输入框")
            
            print("\n⏰ 等待10秒供观察...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            print("✅ 测试完成")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_deepseek_web_search()) 