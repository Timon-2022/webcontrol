#!/usr/bin/env python3
"""
参考链接调试检查器
专门用于分析点击源链接后页面上的所有元素和链接
"""

import asyncio
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_references_after_click():
    """调试点击源链接后的参考链接"""
    print("🔍 参考链接调试检查器")
    print("="*80)
    
    playwright = None
    page = None
    
    try:
        # 1. 启动浏览器（使用持久化数据）
        print("1. 启动浏览器...")
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
        await page.wait_for_timeout(35000)  # 等待35秒
        
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
            await page.wait_for_timeout(8000)  # 等待更长时间
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=f"debug_after_click_{timestamp}.png")
            print(f"✅ 截图已保存: debug_after_click_{timestamp}.png")
        
        # 7. 详细分析页面结构
        print("7. 详细分析页面结构...")
        
        # 7.1 查找所有可能的容器元素
        print("\n📦 查找可能的参考链接容器:")
        container_selectors = [
            "[class*='reference']", "[class*='source']", "[class*='citation']",
            "[class*='panel']", "[class*='sidebar']", "[class*='drawer']",
            "[class*='modal']", "[class*='popup']", "[class*='overlay']",
            "[role='dialog']", "[role='panel']", "[data-testid*='reference']"
        ]
        
        containers_found = []
        for selector in container_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    for i, elem in enumerate(elements):
                        try:
                            text = await elem.inner_text()
                            if text and len(text.strip()) > 10:  # 有实际内容
                                containers_found.append({
                                    'selector': selector,
                                    'index': i,
                                    'text_preview': text[:100]
                                })
                                print(f"  📦 {selector}[{i}]: {text[:60]}...")
                        except:
                            pass
            except:
                continue
        
        # 7.2 查找所有链接
        print(f"\n🔗 查找所有链接:")
        all_links = await page.query_selector_all("a[href]")
        print(f"总共找到 {len(all_links)} 个链接")
        
        external_links = []
        for i, link in enumerate(all_links):
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                
                if href and href.startswith('http') and 'deepseek.com' not in href:
                    external_links.append({
                        'index': i,
                        'url': href,
                        'text': text.strip()[:80]
                    })
                    
                    if len(external_links) <= 20:  # 只显示前20个外部链接
                        print(f"  🔗 {i}: {href}")
                        print(f"      文本: {text.strip()[:60]}...")
                        print()
            except:
                continue
        
        print(f"找到 {len(external_links)} 个外部链接")
        
        # 7.3 检查页面DOM结构
        print(f"\n🌳 分析页面DOM结构:")
        
        # 获取页面的主要结构信息
        dom_info = await page.evaluate("""
            () => {
                const info = {
                    body_children: document.body.children.length,
                    total_elements: document.querySelectorAll('*').length,
                    divs: document.querySelectorAll('div').length,
                    sections: document.querySelectorAll('section').length,
                    articles: document.querySelectorAll('article').length,
                    asides: document.querySelectorAll('aside').length,
                    iframes: document.querySelectorAll('iframe').length,
                    dialogs: document.querySelectorAll('[role="dialog"]').length
                };
                
                // 查找可能包含链接的容器
                const containers_with_links = [];
                const allContainers = document.querySelectorAll('div, section, aside, article');
                
                allContainers.forEach((container, index) => {
                    const links = container.querySelectorAll('a[href]');
                    if (links.length > 2) {  // 包含多个链接的容器
                        containers_with_links.push({
                            tag: container.tagName,
                            class: container.className,
                            links_count: links.length,
                            text_preview: container.textContent.substring(0, 100)
                        });
                    }
                });
                
                info.containers_with_links = containers_with_links.slice(0, 10);  // 只返回前10个
                return info;
            }
        """)
        
        print(f"  📊 页面统计:")
        print(f"    - body子元素: {dom_info['body_children']}")
        print(f"    - 总元素数: {dom_info['total_elements']}")
        print(f"    - div元素: {dom_info['divs']}")
        print(f"    - section元素: {dom_info['sections']}")
        print(f"    - article元素: {dom_info['articles']}")
        print(f"    - aside元素: {dom_info['asides']}")
        print(f"    - iframe元素: {dom_info['iframes']}")
        print(f"    - 对话框元素: {dom_info['dialogs']}")
        
        print(f"\n  📦 包含多个链接的容器:")
        for container in dom_info['containers_with_links']:
            print(f"    - {container['tag']}.{container['class'][:30]}... ({container['links_count']} 个链接)")
            print(f"      内容预览: {container['text_preview']}...")
            print()
        
        # 8. 保存调试结果
        debug_result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'containers_found': containers_found,
            'external_links_count': len(external_links),
            'external_links': external_links[:10],  # 保存前10个
            'dom_info': dom_info
        }
        
        debug_filename = f"debug_references_{timestamp}.json"
        with open(debug_filename, 'w', encoding='utf-8') as f:
            json.dump(debug_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 调试结果已保存: {debug_filename}")
        print("\n🎯 调试总结:")
        print(f"  - 找到 {len(containers_found)} 个可能的参考容器")
        print(f"  - 找到 {len(external_links)} 个外部链接")
        print(f"  - 页面包含 {dom_info['total_elements']} 个DOM元素")
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
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
    asyncio.run(debug_references_after_click()) 