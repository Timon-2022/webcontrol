#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek自动化测试 - 使用保存的登录状态
搜索小鸡科技
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def test_deepseek_auto():
    """DeepSeek自动化测试"""
    print("=" * 70)
    print("🤖 DeepSeek 自动化测试 - 搜索小鸡科技")
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
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            print("✅ 浏览器启动成功")
            context = await browser.new_context(storage_state=login_state)
            page = await context.new_page()
            
            print("�� 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"deepseek_auto_{timestamp}.png")
            print(f"📸 已保存截图")
            
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
                query = "请帮我联网搜索关于'小鸡科技'的最新信息"
                print(f"⌨️ 输入: {query}")
                await input_element.fill(query)
                await page.wait_for_timeout(1000)
                await input_element.press('Enter')
                
                print("⏳ 等待回复...")
                await page.wait_for_timeout(20000)
                
                await page.screenshot(path=f"deepseek_result_{timestamp}.png")
                print("📸 已保存结果截图")
                
                # 获取页面文本
                page_text = await page.text_content('body')
                if '小鸡科技' in page_text:
                    print("✅ 找到相关内容!")
                    lines = [line.strip() for line in page_text.split('\n') if '小鸡科技' in line and len(line.strip()) > 10]
                    for i, line in enumerate(lines[:3]):
                        print(f"  {i+1}. {line[:200]}...")
                else:
                    print("❌ 未找到相关内容")
            else:
                print("❌ 未找到输入框")
            
            await page.wait_for_timeout(10000)
            await browser.close()
            print("✅ 测试完成")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_deepseek_auto())
