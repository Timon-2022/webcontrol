#!/usr/bin/env python3
"""
调试版智能源提取器
"""

import asyncio
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_extraction():
    """调试提取流程"""
    print("🧠 调试版智能源提取器启动")
    
    playwright = None
    browser = None
    page = None
    
    try:
        # 1. 启动浏览器
        print("1. 启动浏览器...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 2. 加载登录状态
        print("2. 加载登录状态...")
        try:
            with open("login_state.json", 'r', encoding='utf-8') as f:
                login_data = json.load(f)
            if 'cookies' in login_data:
                await page.context.add_cookies(login_data['cookies'])
                print("✅ 登录状态加载成功")
        except:
            print("⚠️ 未找到登录状态文件")
        
        # 3. 访问DeepSeek
        print("3. 访问DeepSeek...")
        await page.goto("https://chat.deepseek.com", timeout=30000)
        await page.wait_for_timeout(3000)
        print("✅ 访问成功")
        
        # 4. 发送查询
        print("4. 发送查询...")
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        chat_input = await page.wait_for_selector("textarea", timeout=10000)
        await chat_input.fill(query)
        await chat_input.press('Enter')
        print("✅ 查询发送成功")
        
        # 5. 等待回复
        print("5. 等待回复...")
        await page.wait_for_timeout(30000)  # 等待30秒
        print("✅ 等待完成")
        
        # 6. 查找所有链接
        print("6. 查找所有链接...")
        all_links = await page.query_selector_all("a[href]")
        print(f"✅ 找到 {len(all_links)} 个链接")
        
        # 7. 分析前10个链接
        print("7. 分析前10个链接...")
        for i, link in enumerate(all_links[:10]):
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                print(f"链接 {i+1}: {href} - {text[:50]}...")
            except:
                print(f"链接 {i+1}: 获取失败")
        
        # 8. 保存截图
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"debug_smart_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"✅ 截图已保存: {screenshot_path}")
        
        print("🎉 调试完成")
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭浏览器
        try:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            print("✅ 浏览器已关闭")
        except Exception as e:
            print(f"⚠️ 关闭浏览器时出错: {e}")

if __name__ == "__main__":
    asyncio.run(debug_extraction()) 