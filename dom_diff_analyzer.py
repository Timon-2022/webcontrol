#!/usr/bin/env python3
"""
DOM差异分析器
对比点击源链接前后的页面变化，找出参考链接的位置
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def analyze_dom_changes():
    """分析DOM变化"""
    print("🔄 DOM差异分析器")
    print("对比点击源链接前后的页面变化")
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
        
        # 5. 分析点击前的DOM状态
        print("5. 分析点击前的DOM状态...")
        before_dom = await page.evaluate("""
            () => {
                const result = {
                    total_elements: document.querySelectorAll('*').length,
                    links: [],
                    visible_elements: 0,
                    hidden_elements: 0,
                    modals: [],
                    panels: [],
                    overlays: []
                };
                
                // 统计所有链接
                const allLinks = document.querySelectorAll('a[href]');
                allLinks.forEach(link => {
                    if (link.href && link.href.startsWith('http') && !link.href.includes('deepseek.com')) {
                        result.links.push({
                            href: link.href,
                            text: link.innerText.substring(0, 50),
                            visible: window.getComputedStyle(link).display !== 'none'
                        });
                    }
                });
                
                // 统计可见和隐藏元素
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') {
                        result.hidden_elements++;
                    } else {
                        result.visible_elements++;
                    }
                });
                
                // 查找模态框和面板
                const modalSelectors = ['[role="dialog"]', '.modal', '[class*="modal"]', '[class*="popup"]'];
                modalSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        result.modals.push({
                            selector: selector,
                            visible: window.getComputedStyle(el).display !== 'none',
                            text: el.innerText.substring(0, 100)
                        });
                    });
                });
                
                // 查找面板
                const panelSelectors = ['[class*="panel"]', '[class*="sidebar"]', '[class*="drawer"]'];
                panelSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        result.panels.push({
                            selector: selector,
                            visible: window.getComputedStyle(el).display !== 'none',
                            text: el.innerText.substring(0, 100)
                        });
                    });
                });
                
                return result;
            }
        """)
        
        print(f"  点击前状态:")
        print(f"    总元素数: {before_dom['total_elements']}")
        print(f"    外部链接数: {len(before_dom['links'])}")
        print(f"    可见元素数: {before_dom['visible_elements']}")
        print(f"    隐藏元素数: {before_dom['hidden_elements']}")
        print(f"    模态框数: {len(before_dom['modals'])}")
        print(f"    面板数: {len(before_dom['panels'])}")
        
        # 6. 查找并点击源链接
        print("6. 查找并点击源链接...")
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
            print("7. 点击源链接...")
            await sources_element.click()
            
            # 等待DOM变化
            await page.wait_for_timeout(8000)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=f"dom_diff_{timestamp}.png")
            print(f"✅ 截图已保存: dom_diff_{timestamp}.png")
        
        # 8. 分析点击后的DOM状态
        print("8. 分析点击后的DOM状态...")
        after_dom = await page.evaluate("""
            () => {
                const result = {
                    total_elements: document.querySelectorAll('*').length,
                    links: [],
                    visible_elements: 0,
                    hidden_elements: 0,
                    modals: [],
                    panels: [],
                    overlays: [],
                    new_content: []
                };
                
                // 统计所有链接
                const allLinks = document.querySelectorAll('a[href]');
                allLinks.forEach(link => {
                    if (link.href && link.href.startsWith('http') && !link.href.includes('deepseek.com')) {
                        result.links.push({
                            href: link.href,
                            text: link.innerText.substring(0, 50),
                            visible: window.getComputedStyle(link).display !== 'none'
                        });
                    }
                });
                
                // 统计可见和隐藏元素
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') {
                        result.hidden_elements++;
                    } else {
                        result.visible_elements++;
                    }
                });
                
                // 查找模态框和面板
                const modalSelectors = ['[role="dialog"]', '.modal', '[class*="modal"]', '[class*="popup"]'];
                modalSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        result.modals.push({
                            selector: selector,
                            visible: window.getComputedStyle(el).display !== 'none',
                            text: el.innerText.substring(0, 100)
                        });
                    });
                });
                
                // 查找面板
                const panelSelectors = ['[class*="panel"]', '[class*="sidebar"]', '[class*="drawer"]'];
                panelSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        result.panels.push({
                            selector: selector,
                            visible: window.getComputedStyle(el).display !== 'none',
                            text: el.innerText.substring(0, 100)
                        });
                    });
                });
                
                // 查找可能的新内容区域
                const contentSelectors = ['[class*="reference"]', '[class*="source"]', '[class*="citation"]'];
                contentSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        if (el.innerText.length > 20) {
                            result.new_content.push({
                                selector: selector,
                                visible: window.getComputedStyle(el).display !== 'none',
                                text: el.innerText.substring(0, 200),
                                links_count: el.querySelectorAll('a[href]').length
                            });
                        }
                    });
                });
                
                return result;
            }
        """)
        
        print(f"  点击后状态:")
        print(f"    总元素数: {after_dom['total_elements']}")
        print(f"    外部链接数: {len(after_dom['links'])}")
        print(f"    可见元素数: {after_dom['visible_elements']}")
        print(f"    隐藏元素数: {after_dom['hidden_elements']}")
        print(f"    模态框数: {len(after_dom['modals'])}")
        print(f"    面板数: {len(after_dom['panels'])}")
        print(f"    新内容区域数: {len(after_dom['new_content'])}")
        
        # 9. 计算差异
        print("\n9. 计算DOM差异...")
        diff_result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'before_click': before_dom,
            'after_click': after_dom,
            'differences': {
                'element_count_change': after_dom['total_elements'] - before_dom['total_elements'],
                'link_count_change': len(after_dom['links']) - len(before_dom['links']),
                'visible_element_change': after_dom['visible_elements'] - before_dom['visible_elements'],
                'hidden_element_change': after_dom['hidden_elements'] - before_dom['hidden_elements'],
                'new_links': [],
                'new_modals': [],
                'new_panels': []
            }
        }
        
        # 找出新增的链接
        before_links = set(link['href'] for link in before_dom['links'])
        after_links = set(link['href'] for link in after_dom['links'])
        new_links = after_links - before_links
        diff_result['differences']['new_links'] = list(new_links)
        
        print(f"  📊 变化统计:")
        print(f"    元素数变化: {diff_result['differences']['element_count_change']}")
        print(f"    链接数变化: {diff_result['differences']['link_count_change']}")
        print(f"    可见元素变化: {diff_result['differences']['visible_element_change']}")
        print(f"    隐藏元素变化: {diff_result['differences']['hidden_element_change']}")
        print(f"    新增链接数: {len(new_links)}")
        
        if new_links:
            print(f"  🔗 新增的链接:")
            for link in list(new_links)[:5]:  # 显示前5个
                print(f"    - {link}")
        
        if after_dom['new_content']:
            print(f"  📄 发现的新内容区域:")
            for content in after_dom['new_content'][:3]:  # 显示前3个
                print(f"    - {content['selector']}: {content['links_count']} 个链接")
                print(f"      内容: {content['text'][:100]}...")
        
        # 10. 保存结果
        result_filename = f"dom_diff_analysis_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(diff_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 分析结果已保存: {result_filename}")
        
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
    asyncio.run(analyze_dom_changes()) 