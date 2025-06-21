#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek 登录态复用和联网搜索测试
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

class DeepSeekTester:
    def __init__(self):
        self.browser = None
        self.page = None
        self.login_state_file = "deepseek_login_state.json"
        
    async def init_browser(self, headless=False):
        """初始化浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 创建上下文
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = await context.new_page()
            print("✅ 浏览器初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 浏览器初始化失败: {e}")
            return False
    
    async def save_login_state(self):
        """保存登录状态"""
        try:
            # 获取所有cookies
            cookies = await self.page.context.cookies()
            
            # 获取localStorage
            local_storage = await self.page.evaluate("() => JSON.stringify(localStorage)")
            
            # 获取sessionStorage
            session_storage = await self.page.evaluate("() => JSON.stringify(sessionStorage)")
            
            login_state = {
                'cookies': cookies,
                'localStorage': json.loads(local_storage) if local_storage != '{}' else {},
                'sessionStorage': json.loads(session_storage) if session_storage != '{}' else {},
                'timestamp': datetime.now().isoformat(),
                'url': self.page.url
            }
            
            with open(self.login_state_file, 'w', encoding='utf-8') as f:
                json.dump(login_state, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 登录状态已保存到 {self.login_state_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存登录状态失败: {e}")
            return False
    
    async def load_login_state(self):
        """加载登录状态"""
        try:
            if not os.path.exists(self.login_state_file):
                print(f"❌ 登录状态文件不存在: {self.login_state_file}")
                return False
            
            with open(self.login_state_file, 'r', encoding='utf-8') as f:
                login_state = json.load(f)
            
            # 设置cookies
            if login_state.get('cookies'):
                await self.page.context.add_cookies(login_state['cookies'])
                print("✅ Cookies 已加载")
            
            # 访问DeepSeek页面
            await self.page.goto("https://chat.deepseek.com")
            await self.page.wait_for_timeout(2000)
            
            # 设置localStorage
            if login_state.get('localStorage'):
                for key, value in login_state['localStorage'].items():
                    await self.page.evaluate(f"localStorage.setItem('{key}', '{value}')")
                print("✅ localStorage 已加载")
            
            # 设置sessionStorage
            if login_state.get('sessionStorage'):
                for key, value in login_state['sessionStorage'].items():
                    await self.page.evaluate(f"sessionStorage.setItem('{key}', '{value}')")
                print("✅ sessionStorage 已加载")
            
            # 刷新页面使状态生效
            await self.page.reload()
            await self.page.wait_for_timeout(3000)
            
            return True
            
        except Exception as e:
            print(f"❌ 加载登录状态失败: {e}")
            return False
    
    async def manual_login(self):
        """手动登录"""
        print("🔐 开始手动登录流程...")
        
        # 启动有头浏览器进行手动登录
        await self.close_browser()
        await self.init_browser(headless=False)
        
        # 访问DeepSeek
        await self.page.goto("https://chat.deepseek.com")
        await self.page.wait_for_timeout(3000)
        
        print("📱 请在浏览器中完成登录操作...")
        print("⏰ 登录完成后，请按回车键继续...")
        
        # 等待用户手动登录
        input("按回车键继续...")
        
        # 保存登录状态
        await self.save_login_state()
        
        return True
    
    async def test_login_status(self):
        """测试登录状态"""
        try:
            # 检查是否已登录
            await self.page.wait_for_timeout(2000)
            
            # 查找登录相关元素
            login_indicators = [
                "button:has-text('登录')",
                "button:has-text('Sign in')",
                ".login-button",
                "[data-testid='login']"
            ]
            
            is_logged_in = True
            for selector in login_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        is_logged_in = False
                        break
                except:
                    continue
            
            if is_logged_in:
                print("✅ 已登录状态")
                return True
            else:
                print("❌ 未登录状态")
                return False
                
        except Exception as e:
            print(f"❌ 检查登录状态失败: {e}")
            return False
    
    async def search_with_deepseek(self, query):
        """使用DeepSeek进行联网搜索"""
        try:
            print(f"🔍 开始搜索关键词: {query}")
            
            # 查找输入框
            input_selectors = [
                "textarea[placeholder*='输入']",
                "textarea[placeholder*='问我']",
                "textarea",
                ".chat-input textarea",
                "[data-testid='chat-input']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await self.page.wait_for_selector(selector, timeout=5000)
                    if input_element:
                        print(f"✅ 找到输入框: {selector}")
                        break
                except:
                    continue
            
            if not input_element:
                print("❌ 未找到输入框")
                return []
            
            # 构造搜索提示
            search_prompt = f"请帮我联网搜索关于'{query}'的最新信息，包括公司背景、业务范围、最新动态等详细信息。"
            
            # 输入搜索内容
            await input_element.fill(search_prompt)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            await input_element.press('Enter')
            print("✅ 搜索请求已发送")
            
            # 等待回复
            print("⏳ 等待DeepSeek回复...")
            await self.page.wait_for_timeout(15000)  # 等待15秒
            
            # 获取回复内容
            response_selectors = [
                ".message-content",
                ".chat-message",
                ".response",
                "[data-message-author-role='assistant']",
                ".markdown",
                ".prose"
            ]
            
            results = []
            for selector in response_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for i, element in enumerate(elements[-3:]):  # 获取最后3个回复
                            text = await element.text_content()
                            if text and len(text.strip()) > 50:
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
                    print(f"尝试选择器 {selector} 失败: {e}")
                    continue
            
            if not results:
                print("❌ 未获取到回复内容")
            
            return results
            
        except Exception as e:
            print(f"❌ 搜索过程失败: {e}")
            return []
    
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
        filename = f"data/deepseek_search_{query}_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 结果已保存到: {filename}")
        return filename

async def main():
    """主函数"""
    tester = DeepSeekTester()
    query = "小鸡科技"
    
    print("=" * 50)
    print("🤖 DeepSeek 登录态复用和联网搜索测试")
    print("=" * 50)
    
    try:
        # 初始化浏览器
        if not await tester.init_browser():
            return
        
        # 尝试加载登录状态
        login_loaded = await tester.load_login_state()
        
        if not login_loaded:
            print("🔑 需要手动登录...")
            await tester.manual_login()
        
        # 测试登录状态
        if await tester.test_login_status():
            print("✅ 登录状态正常，开始搜索...")
            
            # 执行搜索
            results = await tester.search_with_deepseek(query)
            
            # 保存结果
            if results:
                filename = tester.save_results(results, query)
                print(f"\n📊 搜索完成！")
                print(f"📁 获取到 {len(results)} 个结果")
                print(f"💾 结果文件: {filename}")
                
                # 显示结果摘要
                for i, result in enumerate(results):
                    print(f"\n📝 结果 {i+1}:")
                    print(f"   标题: {result['title']}")
                    print(f"   内容: {result['content'][:200]}...")
            else:
                print("❌ 未获取到搜索结果")
        else:
            print("❌ 登录状态异常，请重新登录")
            
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
    finally:
        await tester.close_browser()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 