#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def test_chat():
    print("=== 聊天搜索测试 ===")
    
    try:
        playwright = await async_playwright().start()
        
        # 使用更简单的启动参数
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True,
        )
        
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        # 测试访问ChatGPT
        print("正在访问 ChatGPT...")
        await page.goto("https://chat.openai.com", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 检查页面标题
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 保存页面内容用于调试
        content = await page.content()
        with open("debug_chatgpt.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("✓ 页面内容已保存到 debug_chatgpt.html")
        
        # 查找聊天输入框
        try:
            chat_input = await page.wait_for_selector("textarea", timeout=10000)
            if chat_input:
                print("✓ 找到聊天输入框")
                
                # 输入测试消息
                await chat_input.fill("请告诉我关于小鸟科技的信息")
                await page.wait_for_timeout(1000)
                
                # 发送消息
                await chat_input.press('Enter')
                print("✓ 已发送消息")
                
                # 等待回复
                await page.wait_for_timeout(10000)
                print("✓ 等待回复完成")
                
            else:
                print("✗ 未找到聊天输入框")
        except Exception as e:
            print(f"✗ 查找输入框失败: {e}")
        
        await context.close()
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat()) 