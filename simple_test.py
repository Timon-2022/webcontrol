#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from playwright.async_api import async_playwright

async def simple_test():
    """简单的浏览器测试"""
    print("开始测试浏览器...")
    
    try:
        playwright = await async_playwright().start()
        print("✓ Playwright 启动成功")
        
        browser = await playwright.chromium.launch(headless=False)
        print("✓ 浏览器启动成功")
        
        context = await browser.new_context()
        print("✓ 上下文创建成功")
        
        page = await context.new_page()
        print("✓ 页面创建成功")
        
        print("正在打开 ChatGPT...")
        await page.goto("https://chat.openai.com", timeout=30000)
        print("✓ 成功访问 ChatGPT")
        
        title = await page.title()
        print(f"页面标题: {title}")
        
        input("浏览器已打开，请检查是否能看到 ChatGPT 页面。按回车继续...")
        
        await context.close()
        await browser.close()
        await playwright.stop()
        print("✓ 测试完成")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        if 'playwright' in locals():
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(simple_test())
