#!/usr/bin/env python3
"""
高级右侧面板提取器
专门查找搜索结果中的可点击链接和域名，并尝试访问原始网站
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright
import re

async def main():
    """主函数"""
    print("�� 高级右侧面板提取器")
    print("专门查找搜索结果中的可点击链接和域名")
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
            await page.wait_for_timeout(10000)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=f"advanced_right_panel_{timestamp}.png")
            print(f"✅ 截图已保存: advanced_right_panel_{timestamp}.png")
        
        # 7. 提取所有搜索结果中的域名和链接信息
        print("7. 提取搜索结果中的域名和链接...")
        
        # 获取页面上所有文本内容，查找域名模式
        page_content = await page.evaluate("""
            () => {
                const results = [];
                const rightArea = document.querySelectorAll('*');
                
                rightArea.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    
                    // 只考虑右侧区域的元素 (x > 800)
                    if (rect.x > 800 && rect.width > 50 && rect.height > 20) {
                        const text = el.innerText || el.textContent || '';
                        
                        // 查找域名模式
                        const domainPattern = /([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.)+[a-zA-Z]{2,}/g;
                        const domains = text.match(domainPattern) || [];
                        
                        // 查找日期模式
                        const datePattern = /\d{4}\/\d{1,2}\/\d{1,2}/g;
                        const dates = text.match(datePattern) || [];
                        
                        // 查找数字引用模式 (如 "1", "2", "3" 等)
                        const numberPattern = /^\d+$/;
                        const lines = text.split('\\n');
                        const numbers = lines.filter(line => numberPattern.test(line.trim()));
                        
                        if (domains.length > 0 || dates.length > 0 || text.length > 100) {
                            results.push({
                                index: index,
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                text: text.substring(0, 300),
                                domains: domains,
                                dates: dates,
                                numbers: numbers,
                                hasClickableChild: el.querySelector('a, button, [role="button"], [onclick]') !== null
                            });
                        }
                    }
                });
                
                return results;
            }
        """)
        
        print(f"找到 {len(page_content)} 个包含域名或重要信息的元素")
        
        # 8. 分析和整理域名信息
        domain_info = {}
        all_domains = set()
        
        for item in page_content:
            for domain in item['domains']:
                all_domains.add(domain)
                if domain not in domain_info:
                    domain_info[domain] = {
                        'domain': domain,
                        'occurrences': 0,
                        'contexts': [],
                        'dates': set(),
                        'numbers': set()
                    }
                
                domain_info[domain]['occurrences'] += 1
                domain_info[domain]['contexts'].append(item['text'][:200])
                domain_info[domain]['dates'].update(item['dates'])
                domain_info[domain]['numbers'].update(item['numbers'])
        
        # 转换set为list以便JSON序列化
        for domain in domain_info:
            domain_info[domain]['dates'] = list(domain_info[domain]['dates'])
            domain_info[domain]['numbers'] = list(domain_info[domain]['numbers'])
        
        print(f"识别出 {len(all_domains)} 个唯一域名:")
        for domain in sorted(all_domains):
            print(f"  - {domain} (出现 {domain_info[domain]['occurrences']} 次)")
        
        # 9. 尝试访问这些域名对应的网站
        print(f"\\n9. 尝试访问前 {min(10, len(all_domains))} 个域名...")
        
        website_data = []
        domains_to_visit = list(sorted(all_domains, key=lambda d: domain_info[d]['occurrences'], reverse=True))[:10]
        
        for i, domain in enumerate(domains_to_visit):
            try:
                print(f"\\n访问 {i+1}/{len(domains_to_visit)}: {domain}")
                
                # 构造完整URL
                if not domain.startswith('http'):
                    url = f"https://{domain}"
                else:
                    url = domain
                
                # 创建新标签页访问网站
                new_page = await context.new_page()
                
                try:
                    # 设置较短的超时时间
                    await new_page.goto(url, timeout=15000)
                    await new_page.wait_for_load_state('load', timeout=10000)
                    
                    # 提取网站信息
                    site_info = await new_page.evaluate("""
                        () => {
                            return {
                                title: document.title || '',
                                description: (document.querySelector('meta[name="description"]') || {}).content || '',
                                keywords: (document.querySelector('meta[name="keywords"]') || {}).content || '',
                                h1_texts: Array.from(document.querySelectorAll('h1')).map(h => h.innerText).slice(0, 3),
                                h2_texts: Array.from(document.querySelectorAll('h2')).map(h => h.innerText).slice(0, 5),
                                body_preview: document.body ? document.body.innerText.substring(0, 500) : '',
                                links_count: document.querySelectorAll('a[href]').length,
                                images_count: document.querySelectorAll('img').length
                            };
                        }
                    """)
                    
                    website_data.append({
                        'domain': domain,
                        'url': url,
                        'success': True,
                        'info': site_info,
                        'context_from_search': domain_info[domain]['contexts'][0][:200],
                        'search_occurrences': domain_info[domain]['occurrences'],
                        'related_dates': domain_info[domain]['dates'],
                        'related_numbers': domain_info[domain]['numbers']
                    })
                    
                    print(f"  ✅ 成功访问: {site_info['title'][:50]}...")
                    
                except Exception as e:
                    website_data.append({
                        'domain': domain,
                        'url': url,
                        'success': False,
                        'error': str(e),
                        'context_from_search': domain_info[domain]['contexts'][0][:200],
                        'search_occurrences': domain_info[domain]['occurrences']
                    })
                    print(f"  ❌ 访问失败: {str(e)[:50]}...")
                
                finally:
                    await new_page.close()
                
                # 等待一下避免请求过快
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"  ❌ 处理域名 {domain} 时出错: {e}")
        
        # 10. 保存结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'total_domains_found': len(all_domains),
            'domains_attempted': len(domains_to_visit),
            'successful_visits': len([d for d in website_data if d.get('success', False)]),
            'domain_info': domain_info,
            'website_data': website_data,
            'all_domains': list(all_domains)
        }
        
        result_filename = f"advanced_right_panel_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\\n✅ 结果已保存: {result_filename}")
        print(f"\\n🎯 总结:")
        print(f"  - 识别域名: {result['total_domains_found']}")
        print(f"  - 尝试访问: {result['domains_attempted']}")
        print(f"  - 成功访问: {result['successful_visits']}")
        
        if result['successful_visits'] > 0:
            print(f"\\n📄 成功访问的网站:")
            for data in website_data:
                if data.get('success', False):
                    print(f"  ✅ {data['domain']}")
                    print(f"     标题: {data['info']['title'][:60]}...")
                    print(f"     描述: {data['info']['description'][:80]}...")
                    print(f"     在搜索中出现: {data['search_occurrences']} 次")
                    if data['related_dates']:
                        print(f"     相关日期: {', '.join(data['related_dates'][:3])}")
                    print()
        
        print(f"\\n🔗 所有识别的域名:")
        for domain in sorted(all_domains):
            print(f"  - {domain}")
        
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
