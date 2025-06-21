#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改进的DeepSeek测试 - 搜索小鸡科技
包含更好的回复检测和登录处理
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def test_deepseek_improved():
    """改进的DeepSeek测试"""
    print("=" * 60)
    print("🤖 DeepSeek 改进测试 - 搜索小鸡科技")
    print("=" * 60)
    
    try:
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=False,  # 可见模式
                slow_mo=1000,    # 慢动作便于观察
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security'
                ]
            )
            
            print("✅ 浏览器启动成功")
            
            # 创建页面
            page = await browser.new_page()
            page.set_default_timeout(60000)
            
            print("🌐 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            print("✅ 页面加载成功")
            
            # 等待页面完全加载
            await page.wait_for_timeout(5000)
            
            # 获取页面标题
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            # 保存初始页面截图
            await page.screenshot(path="deepseek_initial.png")
            print("📸 已保存初始页面截图: deepseek_initial.png")
            
            # 检查是否需要登录
            print("\n🔍 检查登录状态...")
            login_indicators = [
                "text=登录",
                "text=Sign in",
                "text=Get Started",
                "button:has-text('登录')",
                "button:has-text('Sign in')"
            ]
            
            needs_login = False
            for indicator in login_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=3000)
                    if element and await element.is_visible():
                        needs_login = True
                        print(f"🔑 检测到登录按钮: {indicator}")
                        break
                except:
                    continue
            
            if needs_login:
                print("⚠️ 页面需要登录")
                print("💡 请在浏览器中手动登录，然后按回车键继续...")
                input("登录完成后按回车键继续...")
                
                # 等待登录完成
                await page.wait_for_timeout(3000)
                await page.screenshot(path="deepseek_after_login.png")
                print("📸 已保存登录后截图: deepseek_after_login.png")
            else:
                print("✅ 无需登录或已登录")
            
            # 查找输入框
            print("\n🔍 查找输入框...")
            input_selectors = [
                "textarea[placeholder*='输入']",
                "textarea[placeholder*='问我']",
                "textarea[placeholder*='message']",
                "textarea",
                "input[type='text']",
                ".chat-input textarea",
                "[data-testid='chat-input']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            input_element = element
                            print(f"✅ 找到可用输入框: {selector}")
                            break
                    if input_element:
                        break
                except Exception as e:
                    print(f"尝试选择器 {selector} 失败: {e}")
                    continue
            
            if not input_element:
                print("❌ 未找到可用的输入框")
                await page.screenshot(path="deepseek_no_input.png")
                print("📸 已保存无输入框截图: deepseek_no_input.png")
                return
            
            # 输入搜索内容
            search_query = "请帮我联网搜索关于'小鸡科技'的最新信息，包括公司背景、业务范围、最新动态等详细信息。"
            
            print("⌨️ 输入搜索内容...")
            await input_element.fill(search_query)
            await page.wait_for_timeout(2000)
            
            # 发送消息
            print("📤 发送消息...")
            await input_element.press('Enter')
            
            # 等待回复 - 分阶段等待
            print("⏳ 等待DeepSeek回复...")
            
            # 第一阶段：等待5秒，检查是否有立即回复
            await page.wait_for_timeout(5000)
            await page.screenshot(path="deepseek_5s.png")
            
            # 第二阶段：等待10秒，检查是否有回复开始
            await page.wait_for_timeout(10000)
            await page.screenshot(path="deepseek_15s.png")
            
            # 第三阶段：再等待15秒，总共30秒
            await page.wait_for_timeout(15000)
            await page.screenshot(path="deepseek_30s.png")
            print("📸 已保存各阶段截图")
            
            # 尝试多种方式获取回复
            print("📖 尝试获取回复内容...")
            
            # 方法1：查找所有可能的消息容器
            message_selectors = [
                "[data-testid='message']",
                ".message",
                ".chat-message",
                ".response",
                ".assistant-message",
                ".markdown",
                ".prose",
                "[role='assistant']",
                ".message-content",
                ".msg-content"
            ]
            
            all_messages = []
            for selector in message_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"🔍 选择器 {selector} 找到 {len(elements)} 个元素")
                    
                    for i, element in enumerate(elements):
                        text = await element.text_content()
                        if text and len(text.strip()) > 20:
                            all_messages.append({
                                'selector': selector,
                                'index': i,
                                'text': text.strip(),
                                'length': len(text.strip())
                            })
                            print(f"  📝 消息 {i}: {text[:100]}...")
                except Exception as e:
                    print(f"  ❌ 选择器 {selector} 失败: {e}")
            
            # 方法2：获取页面所有文本，查找可能的回复
            print("\n🔍 分析页面所有文本...")
            try:
                page_text = await page.text_content('body')
                if page_text and '小鸡科技' in page_text:
                    print("✅ 页面中包含'小鸡科技'相关内容")
                    # 提取包含小鸡科技的段落
                    lines = page_text.split('\n')
                    relevant_lines = [line.strip() for line in lines if '小鸡科技' in line and len(line.strip()) > 10]
                    for i, line in enumerate(relevant_lines[:5]):  # 最多显示5行
                        print(f"  📄 相关内容 {i+1}: {line[:200]}...")
                        all_messages.append({
                            'selector': 'page_text',
                            'index': i,
                            'text': line,
                            'length': len(line)
                        })
                else:
                    print("❌ 页面中未找到'小鸡科技'相关内容")
            except Exception as e:
                print(f"❌ 分析页面文本失败: {e}")
            
            # 保存结果
            if all_messages:
                print(f"\n✅ 总共找到 {len(all_messages)} 条可能的回复")
                
                # 保存结果到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/deepseek_improved_test_{timestamp}.json"
                
                os.makedirs("data", exist_ok=True)
                
                result = {
                    'query': '小鸡科技',
                    'timestamp': datetime.now().isoformat(),
                    'page_title': title,
                    'needs_login': needs_login,
                    'total_messages': len(all_messages),
                    'messages': all_messages,
                    'test_type': 'improved_test'
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"💾 结果已保存到: {filename}")
                
                # 显示最相关的回复
                print("\n📝 最相关的回复内容:")
                for i, msg in enumerate(all_messages[:3]):  # 显示前3条
                    print(f"  {i+1}. [{msg['selector']}] {msg['text'][:300]}...")
                    
            else:
                print("❌ 未找到任何回复内容")
                print("💡 可能的原因:")
                print("  - 需要登录验证")
                print("  - 网络问题导致回复延迟")
                print("  - 页面结构发生变化")
                print("  - 需要人机验证")
            
            print("\n⏰ 等待10秒供最终观察...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            print("✅ 浏览器已关闭")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 改进测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_deepseek_improved()) 