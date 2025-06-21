#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek测试 - 支持登录状态保存和复用
搜索小鸡科技
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

# 登录状态保存文件
LOGIN_STATE_FILE = "deepseek_login_state.json"

async def save_login_state(context):
    """保存登录状态"""
    try:
        state = await context.storage_state()
        with open(LOGIN_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"✅ 登录状态已保存到: {LOGIN_STATE_FILE}")
        return True
    except Exception as e:
        print(f"❌ 保存登录状态失败: {e}")
        return False

async def load_login_state():
    """加载登录状态"""
    try:
        if os.path.exists(LOGIN_STATE_FILE):
            with open(LOGIN_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            print(f"✅ 从文件加载登录状态: {LOGIN_STATE_FILE}")
            return state
        else:
            print("ℹ️ 未找到保存的登录状态文件")
            return None
    except Exception as e:
        print(f"❌ 加载登录状态失败: {e}")
        return None

async def test_deepseek_with_login():
    """DeepSeek测试 - 支持登录状态复用"""
    print("=" * 70)
    print("🤖 DeepSeek 登录状态复用测试 - 搜索小鸡科技")
    print("=" * 70)
    
    try:
        async with async_playwright() as p:
            # 尝试加载保存的登录状态
            saved_state = await load_login_state()
            
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=False,  # 可见模式
                slow_mo=500,     # 稍快一些
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security'
                ]
            )
            
            print("✅ 浏览器启动成功")
            
            # 创建浏览器上下文，如果有保存的状态就加载
            if saved_state:
                print("🔄 使用保存的登录状态创建上下文...")
                context = await browser.new_context(storage_state=saved_state)
            else:
                print("🆕 创建新的浏览器上下文...")
                context = await browser.new_context()
            
            # 创建页面
            page = await context.new_page()
            page.set_default_timeout(60000)
            
            print("🌐 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            print("✅ 页面加载成功")
            
            # 等待页面完全加载
            await page.wait_for_timeout(3000)
            
            # 获取页面标题
            title = await page.title()
            print(f"📄 页面标题: {title}")
            
            # 保存当前页面截图
            await page.screenshot(path="deepseek_current_state.png")
            print("📸 已保存当前页面截图: deepseek_current_state.png")
            
            # 检查是否需要登录
            print("\n🔍 检查登录状态...")
            login_indicators = [
                "text=登录",
                "text=Sign in", 
                "text=Get Started",
                "button:has-text('登录')",
                "button:has-text('Sign in')",
                ".login-btn",
                "[data-testid='login']"
            ]
            
            needs_login = False
            for indicator in login_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=2000)
                    if element and await element.is_visible():
                        needs_login = True
                        print(f"🔑 检测到登录按钮: {indicator}")
                        break
                except:
                    continue
            
            if needs_login:
                print("⚠️ 需要登录")
                print("💡 请在浏览器中手动登录...")
                print("🔔 登录完成后，脚本会自动保存登录状态供下次使用")
                input("\n👆 登录完成后按回车键继续...")
                
                # 等待登录完成
                await page.wait_for_timeout(2000)
                
                # 保存登录状态
                await save_login_state(context)
                
                await page.screenshot(path="deepseek_after_login.png")
                print("📸 已保存登录后截图: deepseek_after_login.png")
            else:
                print("✅ 已登录或无需登录")
            
            # 查找输入框
            print("\n🔍 查找输入框...")
            input_selectors = [
                "textarea[placeholder*='输入']",
                "textarea[placeholder*='问我']", 
                "textarea[placeholder*='message']",
                "textarea[placeholder*='Message']",
                "textarea",
                "input[type='text']",
                ".chat-input textarea",
                "[data-testid='chat-input']",
                "[contenteditable='true']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"🔍 选择器 {selector} 找到 {len(elements)} 个元素")
                    
                    for i, element in enumerate(elements):
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        print(f"  元素 {i}: 可见={is_visible}, 可用={is_enabled}")
                        
                        if is_visible and is_enabled:
                            input_element = element
                            print(f"✅ 找到可用输入框: {selector} (元素 {i})")
                            break
                    
                    if input_element:
                        break
                except Exception as e:
                    print(f"  ❌ 选择器 {selector} 失败: {e}")
                    continue
            
            if not input_element:
                print("❌ 未找到可用的输入框")
                await page.screenshot(path="deepseek_no_input.png")
                print("📸 已保存无输入框截图: deepseek_no_input.png")
                
                await browser.close()
                return
            
            # 输入搜索内容
            search_query = "请帮我联网搜索关于'小鸡科技'的最新信息，包括公司背景、业务范围、最新动态等详细信息。"
            
            print(f"⌨️ 输入搜索内容: {search_query[:50]}...")
            
            # 先清空输入框
            await input_element.fill("")
            await page.wait_for_timeout(500)
            
            # 输入内容
            await input_element.fill(search_query)
            await page.wait_for_timeout(1000)
            
            # 保存输入后的截图
            await page.screenshot(path="deepseek_after_input.png")
            print("📸 已保存输入后截图: deepseek_after_input.png")
            
            # 发送消息
            print("📤 发送消息...")
            await input_element.press('Enter')
            
            # 等待回复 - 分阶段等待和检测
            print("⏳ 等待DeepSeek回复...")
            
            for stage in [5, 10, 15, 20]:
                print(f"  ⏰ 等待 {stage} 秒...")
                await page.wait_for_timeout(5000)
                
                # 保存当前阶段截图
                await page.screenshot(path=f"deepseek_{stage}s.png")
                print(f"  📸 已保存 {stage}秒 截图")
                
                # 检查是否有新内容
                try:
                    page_text = await page.text_content('body')
                    if page_text and '小鸡科技' in page_text:
                        print(f"  ✅ 在 {stage}秒 时检测到回复内容!")
                        break
                except:
                    pass
            
            # 尝试获取回复内容
            print("\n📖 尝试获取回复内容...")
            
            # 多种方式获取消息
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
                ".msg-content",
                ".chat-bubble",
                ".reply",
                ".answer"
            ]
            
            all_messages = []
            for selector in message_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
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
            
            # 分析页面全文
            print("\n🔍 分析页面全文...")
            try:
                page_text = await page.text_content('body')
                if page_text and '小鸡科技' in page_text:
                    print("✅ 页面中包含'小鸡科技'相关内容")
                    
                    # 提取包含关键词的段落
                    lines = page_text.split('\n')
                    relevant_lines = []
                    for line in lines:
                        line = line.strip()
                        if '小鸡科技' in line and len(line) > 10:
                            relevant_lines.append(line)
                    
                    print(f"📊 找到 {len(relevant_lines)} 行相关内容")
                    for i, line in enumerate(relevant_lines[:5]):
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
                print(f"\n✅ 总共找到 {len(all_messages)} 条相关内容")
                
                # 保存到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/deepseek_login_test_{timestamp}.json"
                
                os.makedirs("data", exist_ok=True)
                
                result = {
                    'query': '小鸡科技',
                    'timestamp': datetime.now().isoformat(),
                    'page_title': title,
                    'had_saved_login': saved_state is not None,
                    'needed_login': needs_login,
                    'total_messages': len(all_messages),
                    'messages': all_messages,
                    'test_type': 'login_state_test'
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"💾 结果已保存到: {filename}")
                
                # 显示最相关的内容
                print("\n📝 最相关的回复内容:")
                for i, msg in enumerate(all_messages[:3]):
                    print(f"  {i+1}. [{msg['selector']}] {msg['text'][:300]}...")
                    
            else:
                print("❌ 未找到任何相关内容")
            
            print("\n⏰ 等待10秒供最终观察...")
            await page.wait_for_timeout(10000)
            
            # 最终截图
            await page.screenshot(path="deepseek_final.png")
            print("📸 已保存最终截图: deepseek_final.png")
            
            await browser.close()
            print("✅ 浏览器已关闭")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🏁 登录状态复用测试完成")
    print("=" * 70)
    
    if os.path.exists(LOGIN_STATE_FILE):
        print(f"💡 下次运行时将自动使用保存的登录状态: {LOGIN_STATE_FILE}")
    else:
        print("💡 建议：完成登录后，登录状态会自动保存供下次使用")

if __name__ == "__main__":
    asyncio.run(test_deepseek_with_login()) 