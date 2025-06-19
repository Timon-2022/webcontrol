#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    """测试浏览器启动"""
    print("=== 浏览器启动测试 ===")
    
    try:
        playwright = await async_playwright().start()
        print("✓ Playwright 启动成功")
        
        # 使用最简单的启动方式
        browser = await playwright.chromium.launch(headless=False)
        print("✓ 浏览器启动成功")
        
        context = await browser.new_context()
        print("✓ 浏览器上下文创建成功")
        
        page = await context.new_page()
        print("✓ 页面创建成功")
        
        # 访问一个简单的网站测试
        await page.goto("https://www.google.com", timeout=30000)
        print("✓ 成功访问 Google")
        
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 等待用户确认
        input("浏览器测试成功！按回车键关闭...")
        
        await context.close()
        await browser.close()
        await playwright.stop()
        print("✓ 浏览器已关闭")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        if 'playwright' in locals():
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_browser()) 