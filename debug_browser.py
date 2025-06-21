#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的浏览器调试脚本
"""

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    """测试浏览器基本功能"""
    print("🔍 开始测试浏览器...")
    
    try:
        async with async_playwright() as p:
            # 使用最简单的配置启动浏览器
            browser = await p.chromium.launch(
                headless=False,  # 可见模式
                slow_mo=1000,    # 慢动作，便于观察
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            print("✅ 浏览器启动成功")
            
            # 创建页面
            page = await browser.new_page()
            print("✅ 页面创建成功")
            
            # 访问百度（测试网络连接）
            print("🌐 访问百度...")
            await page.goto('https://www.baidu.com', timeout=30000)
            title = await page.title()
            print(f"✅ 百度访问成功，标题: {title}")
            
            # 等待5秒让用户观察
            await page.wait_for_timeout(5000)
            
            # 尝试访问DeepSeek
            print("🌐 访问DeepSeek...")
            await page.goto('https://chat.deepseek.com', timeout=30000)
            await page.wait_for_timeout(3000)
            title = await page.title()
            print(f"✅ DeepSeek访问成功，标题: {title}")
            
            # 查看页面内容
            print("🔍 查找页面元素...")
            
            # 查找各种可能的输入框
            selectors_to_try = [
                'textarea',
                'input[type="text"]',
                '.chat-input',
                '[placeholder*="输入"]',
                '[placeholder*="问我"]',
                '[data-testid="chat-input"]'
            ]
            
            found_elements = []
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ 找到元素 {selector}: {len(elements)} 个")
                        found_elements.append(selector)
                except Exception as e:
                    print(f"❌ 选择器 {selector} 失败: {e}")
            
            if found_elements:
                print(f"📝 总共找到 {len(found_elements)} 种输入元素")
            else:
                print("❌ 未找到任何输入元素")
            
            # 等待用户观察
            print("⏰ 等待10秒，请观察浏览器页面...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            print("✅ 浏览器已关闭")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

async def test_kimi():
    """测试Kimi访问"""
    print("\n🔍 开始测试Kimi...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1000,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            page = await browser.new_page()
            
            # 访问Kimi
            print("🌐 访问Kimi...")
            await page.goto('https://kimi.moonshot.cn', timeout=30000)
            await page.wait_for_timeout(3000)
            title = await page.title()
            print(f"✅ Kimi访问成功，标题: {title}")
            
            # 查找输入框
            selectors_to_try = [
                'textarea',
                'input[type="text"]',
                '.chat-input',
                '[placeholder*="输入"]',
                '[placeholder*="问我"]'
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ 找到Kimi元素 {selector}: {len(elements)} 个")
                except:
                    continue
            
            # 等待观察
            print("⏰ 等待10秒观察Kimi页面...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Kimi测试失败: {e}")

async def main():
    print("=" * 50)
    print("🚀 浏览器调试测试")
    print("=" * 50)
    
    # 测试基本浏览器功能
    await test_browser()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试Kimi
    await test_kimi()
    
    print("\n" + "=" * 50)
    print("🏁 调试测试完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 