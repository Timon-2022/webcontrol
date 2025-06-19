#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_web_search():
    """调试 DeepSeek 联网搜索按钮"""
    print("=== DeepSeek 联网搜索按钮调试 ===")
    
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
        
        print("请在浏览器中点击联网搜索按钮，然后按回车继续...")
        input()
        
        # 分析页面结构
        print("\n=== 查找可能的联网搜索按钮 ===")
        
        # 查找所有按钮和可点击元素
        button_selectors = [
            "button",
            "[role='button']",
            "[class*='button']",
            "[class*='search']",
            "[class*='web']",
            "[class*='internet']",
            "[class*='online']",
            "svg",  # 图标
            "img"   # 图片
        ]
        
        for selector in button_selectors:
            try:
                elements = await page.query_selector_all(selector)
                print(f"\n选择器 '{selector}' 找到 {len(elements)} 个元素")
                
                for i, element in enumerate(elements):
                    try:
                        # 获取元素的文本内容
                        text = await element.inner_text()
                        # 获取元素的属性
                        class_name = await element.get_attribute("class")
                        title = await element.get_attribute("title")
                        aria_label = await element.get_attribute("aria-label")
                        
                        # 检查是否包含相关关键词
                        relevant_keywords = ['search', 'web', 'internet', 'online', '联网', '搜索', '网络']
                        is_relevant = False
                        
                        if text:
                            is_relevant = any(keyword in text.lower() for keyword in relevant_keywords)
                        if title:
                            is_relevant = is_relevant or any(keyword in title.lower() for keyword in relevant_keywords)
                        if aria_label:
                            is_relevant = is_relevant or any(keyword in aria_label.lower() for keyword in relevant_keywords)
                        if class_name:
                            is_relevant = is_relevant or any(keyword in class_name.lower() for keyword in relevant_keywords)
                        
                        if is_relevant or (text and len(text.strip()) > 0):
                            print(f"  元素 {i}:")
                            if text:
                                print(f"    文本: {text.strip()}")
                            if class_name:
                                print(f"    类名: {class_name}")
                            if title:
                                print(f"    标题: {title}")
                            if aria_label:
                                print(f"    aria-label: {aria_label}")
                            
                            # 检查是否可见和可点击
                            is_visible = await element.is_visible()
                            print(f"    可见: {is_visible}")
                            
                    except Exception as e:
                        print(f"    元素 {i} 分析失败: {e}")
                        
            except Exception as e:
                print(f"选择器 '{selector}' 失败: {e}")
        
        # 查找所有包含特定文本的元素
        print("\n=== 查找包含特定文本的元素 ===")
        text_patterns = ['联网', '搜索', 'web', 'search', 'internet', 'online']
        
        for pattern in text_patterns:
            try:
                # 使用 XPath 查找包含特定文本的元素
                xpath = f"//*[contains(text(), '{pattern}')]"
                elements = await page.query_selector_all(f"xpath={xpath}")
                print(f"\n包含 '{pattern}' 的元素: {len(elements)} 个")
                
                for i, element in enumerate(elements[:5]):  # 只显示前5个
                    try:
                        text = await element.inner_text()
                        class_name = await element.get_attribute("class")
                        tag_name = await element.evaluate("el => el.tagName")
                        
                        print(f"  元素 {i} ({tag_name}): {text.strip()}")
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
    asyncio.run(debug_web_search()) 