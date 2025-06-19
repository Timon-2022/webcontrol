#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_deepseek():
    """调试 DeepSeek 页面结构"""
    print("=== DeepSeek 页面结构调试 ===")
    
    if not os.path.exists("login_state.json"):
        print("请先运行 login_manager.py 登录 DeepSeek")
        return
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        
        context = await browser.new_context(storage_state="login_state.json")
        page = await context.new_page()
        
        # 访问 DeepSeek
        await page.goto("https://chat.deepseek.com", timeout=30000)
        await page.wait_for_timeout(3000)
        
        print("请在浏览器中手动发送一条消息，然后按回车继续...")
        input()
        
        # 等待回复
        print("等待回复...")
        await page.wait_for_timeout(15000)
        
        # 分析页面结构
        print("\n=== 页面分析 ===")
        
        # 测试用户提供的选择器
        user_selector = "#root > div > div > div.c3ecdb44 > div._7780f2e > div > div._3919b83 > div > div > div.dad65929 > div._9663006"
        try:
            element = await page.query_selector(user_selector)
            if element:
                text = await element.inner_text()
                print(f"用户选择器内容: {text[:200]}...")
            else:
                print("用户选择器未找到元素")
        except Exception as e:
            print(f"用户选择器错误: {e}")
        
        # 查找所有包含文本的 div 元素
        print("\n=== 查找所有包含文本的 div 元素 ===")
        all_divs = await page.query_selector_all("div")
        
        for i, div in enumerate(all_divs):
            try:
                text = await div.inner_text()
                if text and len(text.strip()) > 20 and len(text.strip()) < 1000:  # 过滤合适的文本长度
                    # 检查是否包含常见的回复关键词
                    if any(keyword in text.lower() for keyword in ['你好', '您好', '谢谢', '问题', '回答', '解释', '关于']):
                        print(f"可能的回复元素 {i}: {text[:100]}...")
                        
                        # 获取元素的类名和属性
                        class_name = await div.get_attribute("class")
                        if class_name:
                            print(f"  类名: {class_name}")
                        
                        # 获取父元素的类名
                        try:
                            parent = await div.query_selector("xpath=..")
                            if parent:
                                parent_class = await parent.get_attribute("class")
                                if parent_class:
                                    print(f"  父元素类名: {parent_class}")
                        except:
                            pass
            except:
                pass
        
        # 查找所有包含特定类名的元素
        print("\n=== 查找特定类名的元素 ===")
        class_patterns = [
            "*[class*='message']",
            "*[class*='response']", 
            "*[class*='content']",
            "*[class*='text']",
            "*[class*='assistant']",
            "*[class*='ai']"
        ]
        
        for pattern in class_patterns:
            try:
                elements = await page.query_selector_all(pattern)
                print(f"\n模式 '{pattern}' 找到 {len(elements)} 个元素")
                
                for j, element in enumerate(elements[-3:]):  # 只显示最后3个
                    try:
                        text = await element.inner_text()
                        if text and len(text.strip()) > 10:
                            print(f"  元素 {j}: {text[:80]}...")
                            class_name = await element.get_attribute("class")
                            if class_name:
                                print(f"    类名: {class_name}")
                    except:
                        pass
            except Exception as e:
                print(f"模式 '{pattern}' 失败: {e}")
        
        input("按回车关闭浏览器...")
        await context.close()
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        print(f"调试过程出错: {e}")

if __name__ == "__main__":
    asyncio.run(debug_deepseek()) 