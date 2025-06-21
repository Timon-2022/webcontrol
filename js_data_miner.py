#!/usr/bin/env python3
"""
JavaScript数据挖掘器
专门查找页面中可能包含参考链接的JavaScript数据结构
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def mine_javascript_data():
    """挖掘JavaScript数据"""
    print("⛏️ JavaScript数据挖掘器")
    print("查找页面中的参考链接数据结构")
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
            await page.screenshot(path=f"js_data_{timestamp}.png")
            print(f"✅ 截图已保存: js_data_{timestamp}.png")
        
        # 7. 挖掘JavaScript数据
        print("7. 挖掘JavaScript数据...")
        
        # 7.1 查找全局变量中的URL
        print("  7.1 查找全局变量中的URL...")
        global_urls = await page.evaluate("""
            () => {
                const urls = [];
                const urlPattern = /https?:\/\/[^\s"'<>]+/g;
                
                // 检查window对象的所有属性
                for (let key in window) {
                    try {
                        const value = window[key];
                        if (typeof value === 'string') {
                            const matches = value.match(urlPattern);
                            if (matches) {
                                matches.forEach(url => {
                                    if (!url.includes('deepseek.com') && !url.includes('intercom') && !url.includes('googleapis')) {
                                        urls.push({
                                            source: 'window.' + key,
                                            url: url,
                                            context: value.substring(0, 200)
                                        });
                                    }
                                });
                            }
                        } else if (typeof value === 'object' && value !== null) {
                            const jsonStr = JSON.stringify(value);
                            const matches = jsonStr.match(urlPattern);
                            if (matches) {
                                matches.forEach(url => {
                                    if (!url.includes('deepseek.com') && !url.includes('intercom') && !url.includes('googleapis')) {
                                        urls.push({
                                            source: 'window.' + key + ' (object)',
                                            url: url,
                                            context: jsonStr.substring(0, 200)
                                        });
                                    }
                                });
                            }
                        }
                    } catch (e) {
                        // 忽略访问错误
                    }
                }
                
                return urls;
            }
        """)
        
        print(f"    找到 {len(global_urls)} 个全局变量中的URL")
        for url_info in global_urls[:5]:  # 显示前5个
            print(f"      - {url_info['url']}")
            print(f"        来源: {url_info['source']}")
        
        # 7.2 查找script标签中的URL
        print("  7.2 查找script标签中的URL...")
        script_urls = await page.evaluate("""
            () => {
                const urls = [];
                const urlPattern = /https?:\/\/[^\s"'<>]+/g;
                const scripts = document.querySelectorAll('script');
                
                scripts.forEach((script, index) => {
                    if (script.textContent) {
                        const matches = script.textContent.match(urlPattern);
                        if (matches) {
                            matches.forEach(url => {
                                if (!url.includes('deepseek.com') && !url.includes('intercom') && !url.includes('googleapis')) {
                                    urls.push({
                                        source: 'script[' + index + ']',
                                        url: url,
                                        context: script.textContent.substring(0, 200)
                                    });
                                }
                            });
                        }
                    }
                });
                
                return urls;
            }
        """)
        
        print(f"    找到 {len(script_urls)} 个script标签中的URL")
        for url_info in script_urls[:5]:  # 显示前5个
            print(f"      - {url_info['url']}")
            print(f"        来源: {url_info['source']}")
        
        # 7.3 查找data属性中的URL
        print("  7.3 查找data属性中的URL...")
        data_urls = await page.evaluate("""
            () => {
                const urls = [];
                const urlPattern = /https?:\/\/[^\s"'<>]+/g;
                const elements = document.querySelectorAll('*');
                
                elements.forEach((element, index) => {
                    // 检查所有data-*属性
                    for (let attr of element.attributes) {
                        if (attr.name.startsWith('data-')) {
                            const matches = attr.value.match(urlPattern);
                            if (matches) {
                                matches.forEach(url => {
                                    if (!url.includes('deepseek.com') && !url.includes('intercom') && !url.includes('googleapis')) {
                                        urls.push({
                                            source: element.tagName + '[' + index + '].' + attr.name,
                                            url: url,
                                            context: attr.value.substring(0, 200)
                                        });
                                    }
                                });
                            }
                        }
                    }
                });
                
                return urls;
            }
        """)
        
        print(f"    找到 {len(data_urls)} 个data属性中的URL")
        for url_info in data_urls[:5]:  # 显示前5个
            print(f"      - {url_info['url']}")
            print(f"        来源: {url_info['source']}")
        
        # 7.4 查找LocalStorage和SessionStorage
        print("  7.4 查找存储中的URL...")
        storage_urls = await page.evaluate("""
            () => {
                const urls = [];
                const urlPattern = /https?:\/\/[^\s"'<>]+/g;
                
                // 检查localStorage
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    const value = localStorage.getItem(key);
                    const matches = value.match(urlPattern);
                    if (matches) {
                        matches.forEach(url => {
                            if (!url.includes('deepseek.com') && !url.includes('intercom') && !url.includes('googleapis')) {
                                urls.push({
                                    source: 'localStorage.' + key,
                                    url: url,
                                    context: value.substring(0, 200)
                                });
                            }
                        });
                    }
                }
                
                // 检查sessionStorage
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    const value = sessionStorage.getItem(key);
                    const matches = value.match(urlPattern);
                    if (matches) {
                        matches.forEach(url => {
                            if (!url.includes('deepseek.com') && !url.includes('intercom') && !url.includes('googleapis')) {
                                urls.push({
                                    source: 'sessionStorage.' + key,
                                    url: url,
                                    context: value.substring(0, 200)
                                });
                            }
                        });
                    }
                }
                
                return urls;
            }
        """)
        
        print(f"    找到 {len(storage_urls)} 个存储中的URL")
        for url_info in storage_urls[:5]:  # 显示前5个
            print(f"      - {url_info['url']}")
            print(f"        来源: {url_info['source']}")
        
        # 7.5 查找网络请求数据
        print("  7.5 查找页面HTML中的URL...")
        html_urls = await page.evaluate("""
            () => {
                const urls = [];
                const urlPattern = /https?:\/\/[^\s"'<>]+/g;
                const html = document.documentElement.outerHTML;
                const matches = html.match(urlPattern);
                
                if (matches) {
                    const uniqueUrls = [...new Set(matches)];
                    uniqueUrls.forEach(url => {
                        if (!url.includes('deepseek.com') && !url.includes('intercom') && !url.includes('googleapis') && !url.includes('.js') && !url.includes('.css')) {
                            urls.push({
                                source: 'HTML content',
                                url: url,
                                context: 'Found in page HTML'
                            });
                        }
                    });
                }
                
                return urls;
            }
        """)
        
        print(f"    找到 {len(html_urls)} 个HTML中的URL")
        for url_info in html_urls[:10]:  # 显示前10个
            print(f"      - {url_info['url']}")
        
        # 8. 合并和分析结果
        all_urls = global_urls + script_urls + data_urls + storage_urls + html_urls
        
        # 去重
        unique_urls = {}
        for url_info in all_urls:
            url = url_info['url']
            if url not in unique_urls:
                unique_urls[url] = url_info
        
        # 按相关性排序
        sorted_urls = []
        for url, info in unique_urls.items():
            score = 0
            url_lower = url.lower()
            context_lower = info['context'].lower()
            
            # 小鸡科技相关
            if '小鸡' in context_lower or 'xiaoji' in url_lower or 'gamesir' in url_lower:
                score += 20
            
            # 新闻和文章网站
            news_domains = ['36kr.com', 'zhihu.com', 'baidu.com', 'sohu.com', 'sina.com', 'qq.com', 'ithome.com']
            for domain in news_domains:
                if domain in url_lower:
                    score += 15
                    break
            
            # 文章路径
            if '/article/' in url_lower or '/news/' in url_lower or '.html' in url_lower:
                score += 10
            
            info['score'] = score
            sorted_urls.append(info)
        
        sorted_urls.sort(key=lambda x: x['score'], reverse=True)
        
        # 9. 保存结果
        mining_result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'total_urls_found': len(unique_urls),
            'global_urls': len(global_urls),
            'script_urls': len(script_urls),
            'data_urls': len(data_urls),
            'storage_urls': len(storage_urls),
            'html_urls': len(html_urls),
            'sorted_urls': sorted_urls[:20]  # 保存前20个最相关的
        }
        
        result_filename = f"js_data_mining_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(mining_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 数据挖掘结果已保存: {result_filename}")
        print(f"\n🎯 挖掘总结:")
        print(f"  - 总共找到 {len(unique_urls)} 个唯一URL")
        print(f"  - 全局变量: {len(global_urls)} 个")
        print(f"  - Script标签: {len(script_urls)} 个")
        print(f"  - Data属性: {len(data_urls)} 个")
        print(f"  - 存储: {len(storage_urls)} 个")
        print(f"  - HTML内容: {len(html_urls)} 个")
        
        if sorted_urls:
            print(f"\n📄 最相关的URL (按得分排序):")
            for i, url_info in enumerate(sorted_urls[:8], 1):
                print(f"  {i}. {url_info['url']}")
                print(f"     得分: {url_info['score']}")
                print(f"     来源: {url_info['source']}")
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
    asyncio.run(mine_javascript_data()) 