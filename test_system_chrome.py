#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用系统Chrome浏览器测试DeepSeek和Kimi
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

class SystemChromeTester:
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def init_browser(self):
        """使用系统Chrome浏览器初始化"""
        try:
            self.playwright = await async_playwright().start()
            
            # 使用系统安装的Chrome
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--user-data-dir=/tmp/chrome_test_profile'
                ]
            )
            
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = await context.new_page()
            print("✅ 系统Chrome浏览器初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 系统Chrome初始化失败: {e}")
            # 如果系统Chrome失败，尝试Firefox
            return await self.init_firefox()
    
    async def init_firefox(self):
        """备选方案：使用Firefox"""
        try:
            self.browser = await self.playwright.firefox.launch(
                headless=False,
                args=['--no-sandbox']
            )
            
            context = await self.browser.new_context()
            self.page = await context.new_page()
            print("✅ Firefox浏览器初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ Firefox初始化也失败: {e}")
            return False
    
    async def test_deepseek(self, query):
        """测试DeepSeek"""
        print(f"\n🤖 测试DeepSeek - 搜索: {query}")
        results = []
        
        try:
            # 访问DeepSeek
            print("🌐 正在访问DeepSeek...")
            await self.page.goto("https://chat.deepseek.com", timeout=30000)
            await self.page.wait_for_timeout(5000)
            
            title = await self.page.title()
            print(f"✅ DeepSeek访问成功，标题: {title}")
            
            # 等待页面完全加载
            print("⏳ 等待页面加载...")
            await self.page.wait_for_timeout(3000)
            
            # 查找输入框
            print("🔍 查找输入框...")
            input_selectors = [
                "textarea",
                "input[type='text']",
                ".chat-input textarea",
                "[placeholder*='输入']",
                "[placeholder*='问我']",
                "[data-testid='chat-input']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # 找到可见的输入框
                        for element in elements:
                            is_visible = await element.is_visible()
                            if is_visible:
                                input_element = element
                                print(f"✅ 找到可见输入框: {selector}")
                                break
                        if input_element:
                            break
                except Exception as e:
                    print(f"尝试选择器 {selector} 失败: {e}")
                    continue
            
            if not input_element:
                print("❌ 未找到输入框")
                print("💡 可能需要登录或页面结构已变化")
                
                # 保存页面截图用于调试
                await self.page.screenshot(path="deepseek_debug.png")
                print("📸 已保存页面截图到 deepseek_debug.png")
                
                # 等待用户观察
                print("⏰ 等待15秒，请观察浏览器页面...")
                await self.page.wait_for_timeout(15000)
                
                return results
            
            # 构造搜索提示
            search_prompt = f"请帮我联网搜索关于'{query}'的最新信息，包括公司背景、业务范围、最新动态等详细信息。"
            
            # 输入搜索内容
            print("⌨️ 输入搜索内容...")
            await input_element.fill(search_prompt)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            await input_element.press('Enter')
            print("✅ 搜索请求已发送")
            
            # 等待回复
            print("⏳ 等待DeepSeek回复（最多30秒）...")
            await self.page.wait_for_timeout(30000)
            
            # 获取回复内容
            print("📖 获取回复内容...")
            response_selectors = [
                ".message-content",
                ".chat-message",
                ".response",
                ".markdown",
                ".prose",
                "[data-testid='message']",
                ".assistant-message"
            ]
            
            for selector in response_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"✅ 找到回复元素 {selector}: {len(elements)} 个")
                        for i, element in enumerate(elements[-2:]):  # 获取最后2个回复
                            text = await element.text_content()
                            if text and len(text.strip()) > 100:
                                result = {
                                    'website': 'DeepSeek',
                                    'query': query,
                                    'title': f'DeepSeek联网搜索回复 {i+1}',
                                    'content': text.strip(),
                                    'timestamp': datetime.now().isoformat(),
                                    'type': 'chat_response'
                                }
                                results.append(result)
                                print(f"✅ 获取到回复 {i+1}: {text[:100]}...")
                        break
                except Exception as e:
                    print(f"尝试回复选择器 {selector} 失败: {e}")
                    continue
            
            if not results:
                print("❌ 未获取到回复内容")
                # 保存页面截图
                await self.page.screenshot(path="deepseek_no_response.png")
                print("📸 已保存无回复页面截图")
                
        except Exception as e:
            print(f"❌ DeepSeek测试失败: {e}")
            
        return results
    
    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
    
    def save_results(self, results, query):
        """保存搜索结果"""
        if not results:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/system_chrome_search_{query}_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'browser': 'System Chrome',
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 结果已保存到: {filename}")
        return filename

async def main():
    """主函数"""
    tester = SystemChromeTester()
    query = "小鸡科技"
    
    print("=" * 60)
    print("🌐 使用系统Chrome测试DeepSeek联网搜索")
    print(f"🔍 搜索关键词: {query}")
    print("=" * 60)
    
    try:
        # 初始化浏览器
        if not await tester.init_browser():
            print("❌ 所有浏览器初始化都失败了")
            return
        
        # 测试DeepSeek
        results = await tester.test_deepseek(query)
        
        # 保存结果
        if results:
            filename = tester.save_results(results, query)
            
            print(f"\n" + "=" * 60)
            print("📊 测试结果")
            print("=" * 60)
            print(f"🔍 搜索关键词: {query}")
            print(f"📁 获取到结果: {len(results)} 个")
            print(f"💾 结果文件: {filename}")
            
            # 显示结果摘要
            for i, result in enumerate(results):
                print(f"\n📝 结果 {i+1}:")
                print(f"   标题: {result['title']}")
                print(f"   内容: {result['content'][:300]}...")
                print(f"   时间: {result['timestamp']}")
        else:
            print(f"\n❌ 未获取到搜索结果")
            print("💡 请检查浏览器窗口，可能需要手动登录或处理验证")
            
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
    finally:
        print("\n⏰ 等待5秒后关闭浏览器...")
        await asyncio.sleep(5)
        await tester.close_browser()
    
    print(f"\n" + "=" * 60)
    print("🏁 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 