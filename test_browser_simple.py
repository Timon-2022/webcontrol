#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    """最简单的浏览器测试"""
    print("开始测试浏览器...")
    
    try:
        print("1. 启动 Playwright...")
        playwright = await async_playwright().start()
        print("✓ Playwright 启动成功")
        
        print("2. 启动浏览器...")
        browser = await playwright.chromium.launch(headless=False)
        print("✓ 浏览器启动成功")
        
        print("3. 创建上下文...")
        context = await browser.new_context()
        print("✓ 上下文创建成功")
        
        print("4. 创建页面...")
        page = await context.new_page()
        print("✓ 页面创建成功")
        
        print("5. 访问网站...")
        await page.goto("https://www.google.com", timeout=30000)
        print("✓ 成功访问 Google")
        
        title = await page.title()
        print(f"页面标题: {title}")
        
        input("浏览器测试成功！按回车键关闭...")
        
        await context.close()
        await browser.close()
        await playwright.stop()
        print("✓ 浏览器已关闭")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        if 'playwright' in locals():
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_browser()) 