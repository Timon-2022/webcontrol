#!/usr/bin/env python3
"""
iframe参考链接提取器
专门处理iframe中的参考链接提取
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from playwright.async_api import async_playwright
import re
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    print("🖼️ iframe参考链接提取器")
    print("专门处理iframe中的参考链接")
    print("="*80)
    
    playwright = None
    page = None
    
    try:
        # 1. 启动浏览器
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir="./deepseek_user_data",
            headless=False
        )
        
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        # 2. 访问DeepSeek
        print("2. 访问DeepSeek...")
        await page.goto("https://chat.deepseek.com", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 3. 发送查询
        print("3. 发送查询...")
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        chat_input = await page.wait_for_selector("textarea", timeout=10000)
        await chat_input.fill(query)
        await chat_input.press('Enter')
        
        # 4. 等待回复完成
        print("4. 等待回复完成...")
        await page.wait_for_timeout(40000)
        
        # 5. 查找并点击源链接
        print("5. 查找并点击源链接...")
        sources_element = None
        selectors = ["text=已搜索到", "[class*='source']", "text=/已搜索到\\d+个网页/"]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if '搜索到' in text and ('网页' in text or '个' in text):
                        sources_element = element
                        print(f"✅ 找到源信息: {text}")
                        break
                if sources_element:
                    break
            except:
                continue
        
        if sources_element:
            print("6. 点击源链接...")
            await sources_element.click()
            await page.wait_for_timeout(10000)  # 等待10秒
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=f"iframe_click_{timestamp}.png")
            print(f"✅ 截图已保存: iframe_click_{timestamp}.png")
        
        # 7. 查找iframe
        print("7. 查找iframe...")
        iframes = await page.query_selector_all("iframe")
        print(f"找到 {len(iframes)} 个iframe")
        
        all_references = []
        
        # 8. 分析每个iframe
        for i, iframe_element in enumerate(iframes):
            try:
                print(f"8.{i+1} 分析第 {i+1} 个iframe...")
                
                # 获取iframe的frame对象
                iframe_frame = await iframe_element.content_frame()
                if iframe_frame:
                    # 等待iframe加载
                    await iframe_frame.wait_for_load_state('load')
                    await iframe_frame.wait_for_timeout(3000)
                    
                    # 查找iframe中的链接
                    iframe_links = await iframe_frame.query_selector_all("a[href]")
                    print(f"  iframe {i+1} 中找到 {len(iframe_links)} 个链接")
                    
                    for j, link in enumerate(iframe_links):
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            
                            if href and href.startswith('http') and 'deepseek.com' not in href:
                                all_references.append({
                                    'iframe_index': i+1,
                                    'link_index': j+1,
                                    'url': href,
                                    'text': text.strip()[:80],
                                    'domain': urlparse(href).netloc
                                })
                                
                                print(f"    🔗 链接 {j+1}: {href}")
                                print(f"        文本: {text.strip()[:60]}...")
                        except:
                            continue
                
            except Exception as e:
                print(f"  ❌ 分析iframe {i+1} 失败: {e}")
                continue
        
        # 9. 保存结果
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'iframes_found': len(iframes),
            'total_references': len(all_references),
            'references': all_references
        }
        
        result_filename = f"iframe_result_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 结果已保存: {result_filename}")
        print(f"🎯 总结:")
        print(f"  - 找到 {len(iframes)} 个iframe")
        print(f"  - 提取到 {len(all_references)} 个外部链接")
        
        if all_references:
            print(f"\n📄 提取到的链接:")
            for ref in all_references[:10]:  # 显示前10个
                print(f"  🔗 {ref['url']}")
                print(f"      文本: {ref['text']}")
                print(f"      域名: {ref['domain']}")
                print()
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            if page and page.context:
                await page.context.close()
            if playwright:
                await playwright.stop()
            print("✅ 浏览器已关闭")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())