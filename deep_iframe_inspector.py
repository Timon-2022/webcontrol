#!/usr/bin/env python3
"""
深度iframe检查器
详细分析iframe的内容、结构和可能的参考链接
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def deep_inspect_iframe():
    """深度检查iframe内容"""
    print("🔍 深度iframe检查器")
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
            await page.screenshot(path=f"deep_iframe_{timestamp}.png")
            print(f"✅ 截图已保存: deep_iframe_{timestamp}.png")
        
        # 7. 详细分析iframe
        print("7. 详细分析iframe...")
        iframes = await page.query_selector_all("iframe")
        print(f"找到 {len(iframes)} 个iframe")
        
        inspection_result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'iframes_count': len(iframes),
            'iframe_details': []
        }
        
        for i, iframe_element in enumerate(iframes):
            try:
                print(f"\n🔍 检查第 {i+1} 个iframe:")
                
                iframe_info = {
                    'index': i+1,
                    'attributes': {},
                    'content_accessible': False,
                    'content_details': {},
                    'error': None
                }
                
                # 获取iframe属性
                try:
                    src = await iframe_element.get_attribute('src')
                    width = await iframe_element.get_attribute('width')
                    height = await iframe_element.get_attribute('height')
                    name = await iframe_element.get_attribute('name')
                    id_attr = await iframe_element.get_attribute('id')
                    class_attr = await iframe_element.get_attribute('class')
                    
                    iframe_info['attributes'] = {
                        'src': src,
                        'width': width,
                        'height': height,
                        'name': name,
                        'id': id_attr,
                        'class': class_attr
                    }
                    
                    print(f"  📄 iframe属性:")
                    print(f"    src: {src}")
                    print(f"    width: {width}")
                    print(f"    height: {height}")
                    print(f"    name: {name}")
                    print(f"    id: {id_attr}")
                    print(f"    class: {class_attr}")
                    
                except Exception as e:
                    print(f"  ❌ 获取iframe属性失败: {e}")
                
                # 尝试访问iframe内容
                try:
                    iframe_frame = await iframe_element.content_frame()
                    if iframe_frame:
                        iframe_info['content_accessible'] = True
                        print(f"  ✅ iframe内容可访问")
                        
                        # 等待iframe加载
                        await iframe_frame.wait_for_load_state('load', timeout=10000)
                        await iframe_frame.wait_for_timeout(3000)
                        
                        # 获取iframe的基本信息
                        try:
                            iframe_url = iframe_frame.url
                            iframe_title = await iframe_frame.title()
                            
                            iframe_info['content_details']['url'] = iframe_url
                            iframe_info['content_details']['title'] = iframe_title
                            
                            print(f"    URL: {iframe_url}")
                            print(f"    标题: {iframe_title}")
                            
                            # 获取iframe的HTML内容
                            iframe_html = await iframe_frame.content()
                            iframe_info['content_details']['html_length'] = len(iframe_html)
                            iframe_info['content_details']['html_preview'] = iframe_html[:500]
                            
                            print(f"    HTML长度: {len(iframe_html)} 字符")
                            print(f"    HTML预览: {iframe_html[:200]}...")
                            
                            # 查找所有元素
                            all_elements = await iframe_frame.query_selector_all("*")
                            iframe_info['content_details']['total_elements'] = len(all_elements)
                            print(f"    总元素数: {len(all_elements)}")
                            
                            # 查找所有链接
                            all_links = await iframe_frame.query_selector_all("a")
                            iframe_info['content_details']['total_links'] = len(all_links)
                            print(f"    链接数: {len(all_links)}")
                            
                            # 查找有href的链接
                            href_links = await iframe_frame.query_selector_all("a[href]")
                            iframe_info['content_details']['href_links'] = len(href_links)
                            print(f"    有href的链接数: {len(href_links)}")
                            
                            # 查找所有文本内容
                            body_text = await iframe_frame.evaluate("document.body ? document.body.innerText : ''")
                            iframe_info['content_details']['body_text_length'] = len(body_text)
                            iframe_info['content_details']['body_text_preview'] = body_text[:300]
                            
                            print(f"    页面文本长度: {len(body_text)} 字符")
                            if body_text:
                                print(f"    页面文本预览: {body_text[:150]}...")
                            
                            # 检查是否有特殊的数据结构
                            script_elements = await iframe_frame.query_selector_all("script")
                            iframe_info['content_details']['script_count'] = len(script_elements)
                            print(f"    脚本元素数: {len(script_elements)}")
                            
                            # 查找可能的数据属性
                            data_elements = await iframe_frame.query_selector_all("[data-*]")
                            iframe_info['content_details']['data_elements'] = len(data_elements)
                            print(f"    数据属性元素数: {len(data_elements)}")
                            
                        except Exception as e:
                            print(f"    ❌ 获取iframe详细信息失败: {e}")
                            iframe_info['content_details']['error'] = str(e)
                    
                    else:
                        print(f"  ❌ iframe内容不可访问")
                        iframe_info['content_accessible'] = False
                        
                except Exception as e:
                    print(f"  ❌ 访问iframe内容失败: {e}")
                    iframe_info['error'] = str(e)
                
                inspection_result['iframe_details'].append(iframe_info)
                
            except Exception as e:
                print(f"  ❌ 检查iframe {i+1} 失败: {e}")
        
        # 8. 保存检查结果
        result_filename = f"deep_iframe_inspection_{timestamp}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(inspection_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 检查结果已保存: {result_filename}")
        
        # 9. 总结
        print(f"\n🎯 检查总结:")
        print(f"  - 找到 {len(iframes)} 个iframe")
        accessible_count = sum(1 for iframe in inspection_result['iframe_details'] if iframe['content_accessible'])
        print(f"  - 可访问的iframe: {accessible_count}")
        
        for iframe in inspection_result['iframe_details']:
            if iframe['content_accessible']:
                details = iframe['content_details']
                print(f"  - iframe {iframe['index']}: {details.get('total_elements', 0)} 个元素, {details.get('href_links', 0)} 个链接")
        
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
    asyncio.run(deep_inspect_iframe()) 