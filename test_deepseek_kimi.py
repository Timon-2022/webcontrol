#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek 和 Kimi 联网搜索测试
关键词：小鸡科技
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

class AITester:
    def __init__(self):
        self.browser = None
        self.page = None
        
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
            
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.page = await context.new_page()
            print("✅ 浏览器初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 浏览器初始化失败: {e}")
            return False
    
    async def test_deepseek(self, query):
        """测试DeepSeek"""
        print(f"\n🤖 测试DeepSeek - 搜索: {query}")
        results = []
        
        try:
            # 访问DeepSeek
            await self.page.goto("https://chat.deepseek.com", timeout=30000)
            await self.page.wait_for_timeout(5000)
            
            print("📱 访问DeepSeek成功")
            
            # 查找输入框
            input_selectors = [
                "textarea",
                "input[type='text']",
                ".chat-input",
                "[placeholder*='输入']",
                "[placeholder*='问我']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if input_element:
                        print(f"✅ 找到输入框: {selector}")
                        break
                except:
                    continue
            
            if not input_element:
                print("❌ 未找到输入框，可能需要登录")
                return results
            
            # 构造搜索提示
            search_prompt = f"请帮我联网搜索关于'{query}'的最新信息，包括公司背景、业务范围、最新动态等。"
            
            # 输入搜索内容
            await input_element.fill(search_prompt)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            await input_element.press('Enter')
            print("✅ 搜索请求已发送")
            
            # 等待回复
            print("⏳ 等待DeepSeek回复...")
            await self.page.wait_for_timeout(20000)  # 等待20秒
            
            # 获取回复内容
            response_selectors = [
                ".message-content",
                ".chat-message", 
                ".response",
                ".markdown",
                ".prose",
                "[data-testid='message']"
            ]
            
            for selector in response_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for element in elements[-2:]:  # 获取最后2个回复
                            text = await element.text_content()
                            if text and len(text.strip()) > 100:
                                result = {
                                    'website': 'DeepSeek',
                                    'query': query,
                                    'title': 'DeepSeek联网搜索回复',
                                    'content': text.strip(),
                                    'timestamp': datetime.now().isoformat(),
                                    'type': 'chat_response'
                                }
                                results.append(result)
                                print(f"✅ 获取到DeepSeek回复: {text[:100]}...")
                        break
                except Exception as e:
                    continue
            
            if not results:
                print("❌ 未获取到DeepSeek回复")
                
        except Exception as e:
            print(f"❌ DeepSeek测试失败: {e}")
            
        return results
    
    async def test_kimi(self, query):
        """测试Kimi"""
        print(f"\n🤖 测试Kimi - 搜索: {query}")
        results = []
        
        try:
            # 访问Kimi
            await self.page.goto("https://kimi.moonshot.cn", timeout=30000)
            await self.page.wait_for_timeout(5000)
            
            print("📱 访问Kimi成功")
            
            # 查找输入框
            input_selectors = [
                "textarea",
                "input[type='text']",
                ".chat-input",
                "[placeholder*='输入']",
                "[placeholder*='问我']",
                "[data-testid='chat-input']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if input_element:
                        print(f"✅ 找到输入框: {selector}")
                        break
                except:
                    continue
            
            if not input_element:
                print("❌ 未找到输入框，可能需要登录")
                return results
            
            # 构造搜索提示
            search_prompt = f"请帮我联网搜索关于'{query}'的最新信息，包括公司背景、业务范围、最新动态等。"
            
            # 输入搜索内容
            await input_element.fill(search_prompt)
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            await input_element.press('Enter')
            print("✅ 搜索请求已发送")
            
            # 等待回复
            print("⏳ 等待Kimi回复...")
            await self.page.wait_for_timeout(20000)  # 等待20秒
            
            # 获取回复内容
            response_selectors = [
                ".message-content",
                ".chat-message",
                ".response", 
                ".markdown",
                ".prose",
                "[data-testid='message']"
            ]
            
            for selector in response_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for element in elements[-2:]:  # 获取最后2个回复
                            text = await element.text_content()
                            if text and len(text.strip()) > 100:
                                result = {
                                    'website': 'Kimi',
                                    'query': query,
                                    'title': 'Kimi联网搜索回复',
                                    'content': text.strip(),
                                    'timestamp': datetime.now().isoformat(),
                                    'type': 'chat_response'
                                }
                                results.append(result)
                                print(f"✅ 获取到Kimi回复: {text[:100]}...")
                        break
                except Exception as e:
                    continue
            
            if not results:
                print("❌ 未获取到Kimi回复")
                
        except Exception as e:
            print(f"❌ Kimi测试失败: {e}")
            
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
        filename = f"data/ai_search_{query}_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'websites_tested': ['DeepSeek', 'Kimi'],
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 结果已保存到: {filename}")
        return filename

async def main():
    """主函数"""
    tester = AITester()
    query = "小鸡科技"
    
    print("=" * 60)
    print("🤖 DeepSeek 和 Kimi 联网搜索测试")
    print(f"🔍 搜索关键词: {query}")
    print("=" * 60)
    
    all_results = []
    
    try:
        # 初始化浏览器
        if not await tester.init_browser():
            return
        
        # 测试DeepSeek
        deepseek_results = await tester.test_deepseek(query)
        all_results.extend(deepseek_results)
        
        # 等待一下再测试下一个
        await asyncio.sleep(3)
        
        # 测试Kimi
        kimi_results = await tester.test_kimi(query)
        all_results.extend(kimi_results)
        
        # 保存结果
        if all_results:
            filename = tester.save_results(all_results, query)
            
            print(f"\n" + "=" * 60)
            print("📊 测试结果总结")
            print("=" * 60)
            print(f"🔍 搜索关键词: {query}")
            print(f"📁 总共获取: {len(all_results)} 个结果")
            print(f"🤖 DeepSeek结果: {len(deepseek_results)} 个")
            print(f"🤖 Kimi结果: {len(kimi_results)} 个")
            print(f"💾 结果文件: {filename}")
            
            # 显示结果摘要
            for i, result in enumerate(all_results):
                print(f"\n📝 结果 {i+1} ({result['website']}):")
                print(f"   标题: {result['title']}")
                print(f"   内容: {result['content'][:200]}...")
                print(f"   时间: {result['timestamp']}")
        else:
            print(f"\n❌ 未获取到任何搜索结果")
            print("💡 可能的原因:")
            print("   1. 网站需要登录")
            print("   2. 网站有反爬虫机制")
            print("   3. 网络连接问题")
            print("   4. 页面结构发生变化")
            
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
    finally:
        await tester.close_browser()
    
    print(f"\n" + "=" * 60)
    print("🏁 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 