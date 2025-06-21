#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试DeepSeek源链接点击功能
假设已经有了搜索结果，直接测试点击源链接部分
"""

import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def quick_test_sources_click():
    """快速测试点击源链接功能"""
    print("="*60)
    print("快速测试DeepSeek源链接点击功能")
    print("="*60)
    
    # 检查登录状态
    if not os.path.exists("login_state.json"):
        print("⚠️  需要登录状态文件")
        return
    
    playwright = await async_playwright().start()
    
    try:
        # 启动浏览器
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            storage_state="login_state.json",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        # 访问DeepSeek
        print("正在访问DeepSeek...")
        await page.goto("https://chat.deepseek.com")
        await page.wait_for_timeout(3000)
        
        print("请手动:")
        print("1. 输入一个需要联网搜索的问题")
        print("2. 等待AI回复完成")
        print("3. 然后按回车继续，程序将自动查找和点击源链接")
        
        input("准备好后按回车继续...")
        
        # 保存当前页面截图
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        await page.screenshot(path=f"before_sources_click_{timestamp}.png")
        print(f"已保存截图: before_sources_click_{timestamp}.png")
        
        # 查找包含"搜索到"的文本
        print("正在查找源链接...")
        
        # 方法1: 通过文本查找
        try:
            # 查找包含"搜索到"和"网页"的元素
            elements = await page.query_selector_all("*")
            sources_element = None
            sources_text = ""
            
            for element in elements:
                try:
                    text = await element.inner_text()
                    if text and "搜索到" in text and "网页" in text:
                        sources_element = element
                        sources_text = text
                        print(f"找到源文本: {text}")
                        break
                except:
                    continue
            
            if sources_element:
                print("尝试点击源链接...")
                await sources_element.click()
                await page.wait_for_timeout(3000)
                
                # 保存点击后截图
                await page.screenshot(path=f"after_sources_click_{timestamp}.png")
                print(f"已保存截图: after_sources_click_{timestamp}.png")
                
                # 尝试提取URL
                print("正在提取URL...")
                urls = []
                
                # 查找所有链接
                links = await page.query_selector_all("a[href^='http']")
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        if href and href.startswith('http'):
                            urls.append({
                                'url': href,
                                'title': text.strip() if text else href
                            })
                    except:
                        continue
                
                print(f"找到 {len(urls)} 个URL:")
                for i, url_info in enumerate(urls[:10], 1):
                    print(f"{i}. {url_info['title'][:50]}...")
                    print(f"   {url_info['url']}")
                
                # 保存结果
                result = {
                    'timestamp': timestamp,
                    'sources_text': sources_text,
                    'urls_count': len(urls),
                    'urls': urls
                }
                
                result_file = f"sources_result_{timestamp}.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ 结果已保存: {result_file}")
                
            else:
                print("❌ 未找到包含'搜索到'的源链接")
                
                # 显示页面中包含"搜索"的所有文本
                page_content = await page.content()
                matches = re.findall(r'[^>]*搜索[^<]*', page_content)
                if matches:
                    print("页面中包含'搜索'的文本:")
                    for match in matches[:5]:
                        print(f"  - {match}")
        
        except Exception as e:
            print(f"❌ 查找源链接时出错: {e}")
        
        print("\n测试完成，浏览器将保持打开状态供您查看")
        input("按回车关闭浏览器...")
        
    except Exception as e:
        print(f"❌ 测试出错: {e}")
    
    finally:
        await browser.close()
        await playwright.stop()


async def main():
    """主函数"""
    print("DeepSeek源链接快速测试")
    print("="*60)
    print("此测试需要您:")
    print("1. 已经有登录状态文件 login_state.json")
    print("2. 手动输入需要联网搜索的问题")
    print("3. 等待AI回复完成后，程序自动查找和点击源链接")
    print()
    
    confirm = input("是否继续？(y/n): ").strip().lower()
    if confirm == 'y':
        await quick_test_sources_click()
    else:
        print("测试已取消")


if __name__ == "__main__":
    asyncio.run(main()) 