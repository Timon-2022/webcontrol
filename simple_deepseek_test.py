#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单稳定的DeepSeek测试
关键词：小鸡科技
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def test_deepseek_simple():
    """简单测试DeepSeek"""
    print("=" * 50)
    print("🤖 DeepSeek 简单测试")
    print("🔍 搜索关键词: 小鸡科技")
    print("=" * 50)
    
    try:
        async with async_playwright() as p:
            # 使用最稳定的配置
            browser = await p.chromium.launch(
                headless=False,  # 可见模式
                slow_mo=2000,    # 慢动作
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            print("✅ 浏览器启动成功")
            
            # 创建页面
            page = await browser.new_page()
            
            # 设置较长的超时时间
            page.set_default_timeout(60000)
            
            print("🌐 访问DeepSeek...")
            
            # 访问DeepSeek
            await page.goto("https://chat.deepseek.com")
            print("✅ 页面加载成功")
            
            # 等待页面完全加载
            await page.wait_for_timeout(5000)
            
            # 获取页面标题
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            # 保存页面截图
            await page.screenshot(path="deepseek_page.png")
            print("📸 已保存页面截图: deepseek_page.png")
            
            print("\n🔍 查找页面元素...")
            
            # 查找所有可能的输入元素
            selectors = [
                "textarea",
                "input[type='text']",
                ".chat-input",
                "[placeholder*='输入']",
                "[placeholder*='问我']",
                "[data-testid='chat-input']"
            ]
            
            found_inputs = []
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for i, element in enumerate(elements):
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            print(f"✅ 找到元素 {selector}[{i}]: 可见={is_visible}, 可用={is_enabled}")
                            if is_visible and is_enabled:
                                found_inputs.append((selector, element))
                except Exception as e:
                    print(f"❌ 选择器 {selector} 失败: {e}")
            
            if found_inputs:
                print(f"\n📝 找到 {len(found_inputs)} 个可用输入框")
                
                # 使用第一个可用的输入框
                selector, input_element = found_inputs[0]
                print(f"🎯 使用输入框: {selector}")
                
                # 输入测试内容
                test_message = "请帮我联网搜索关于'小鸡科技'的最新信息，包括公司背景、业务范围、最新动态等详细信息。"
                
                print("⌨️ 输入搜索内容...")
                await input_element.fill(test_message)
                await page.wait_for_timeout(2000)
                
                # 发送消息
                print("📤 发送消息...")
                await input_element.press('Enter')
                
                print("⏳ 等待回复（30秒）...")
                await page.wait_for_timeout(30000)
                
                # 保存发送后的页面截图
                await page.screenshot(path="deepseek_after_send.png")
                print("📸 已保存发送后截图: deepseek_after_send.png")
                
                # 尝试获取回复
                print("📖 查找回复内容...")
                response_selectors = [
                    ".message",
                    ".chat-message",
                    ".response",
                    ".markdown",
                    "[data-testid='message']"
                ]
                
                all_messages = []
                for selector in response_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            text = await element.text_content()
                            if text and len(text.strip()) > 20:
                                all_messages.append(text.strip())
                    except:
                        continue
                
                if all_messages:
                    print(f"✅ 找到 {len(all_messages)} 条消息")
                    
                    # 保存结果
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"data/deepseek_simple_test_{timestamp}.json"
                    
                    os.makedirs("data", exist_ok=True)
                    
                    result = {
                        'query': '小鸡科技',
                        'timestamp': datetime.now().isoformat(),
                        'page_title': title,
                        'messages': all_messages,
                        'test_type': 'simple_test'
                    }
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    print(f"💾 结果已保存到: {filename}")
                    
                    # 显示前几条消息
                    print("\n📝 消息内容预览:")
                    for i, msg in enumerate(all_messages[-3:]):  # 显示最后3条
                        print(f"  {i+1}. {msg[:200]}...")
                        
                else:
                    print("❌ 未找到回复消息")
                    
            else:
                print("❌ 未找到可用的输入框")
                print("💡 可能需要登录或页面结构已变化")
            
            print("\n⏰ 等待10秒供观察...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            print("✅ 浏览器已关闭")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_deepseek_simple()) 