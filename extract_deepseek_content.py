#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
提取DeepSeek回复的完整内容
分析搜索结果的详细信息
"""

import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def extract_complete_content():
    """提取DeepSeek的完整回复内容"""
    print("=" * 70)
    print("📖 DeepSeek 完整内容提取 - 分析搜索回复")
    print("=" * 70)
    
    # 加载登录状态
    login_files = ["deepseek_login_state.json", "login_state.json"]
    login_state = None
    
    for file in login_files:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                login_state = json.load(f)
            print(f"✅ 加载登录状态: {file}")
            break
    
    if not login_state:
        print("⚠️ 未找到登录状态文件")
        return
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(storage_state=login_state)
            page = await context.new_page()
            
            print("🌐 访问DeepSeek...")
            await page.goto("https://chat.deepseek.com")
            await page.wait_for_timeout(3000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 点击联网搜索
            print("🔍 启用联网搜索...")
            web_search_btn = await page.wait_for_selector("text=联网搜索", timeout=10000)
            await web_search_btn.click()
            await page.wait_for_timeout(2000)
            
            # 输入搜索
            print("⌨️ 输入搜索内容...")
            input_box = await page.wait_for_selector("textarea", timeout=10000)
            query = "小鸡科技的详细信息，包括公司背景、主要业务、发展历程、最新动态"
            await input_box.fill(query)
            await page.wait_for_timeout(1000)
            await input_box.press('Enter')
            
            print("⏳ 等待搜索和回复完成...")
            await page.wait_for_timeout(15000)  # 等待15秒
            
            # 获取所有消息内容
            print("📖 提取所有消息内容...")
            
            # 尝试多种方式获取回复内容
            message_selectors = [
                ".message-content",
                ".chat-message",
                ".response",
                ".markdown",
                "[role='assistant']",
                ".assistant-message",
                ".prose"
            ]
            
            all_messages = []
            for selector in message_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"🔍 选择器 '{selector}' 找到 {len(elements)} 个消息")
                    
                    for i, element in enumerate(elements):
                        text = await element.text_content()
                        if text and len(text.strip()) > 50:  # 只要较长的内容
                            all_messages.append({
                                'selector': selector,
                                'index': i,
                                'content': text.strip(),
                                'length': len(text.strip())
                            })
                            print(f"  消息 {i}: {len(text)} 字符")
                except Exception as e:
                    print(f"❌ 选择器 {selector} 失败: {e}")
            
            # 获取完整页面文本
            print("\n📄 获取完整页面文本...")
            full_page_text = await page.text_content('body')
            
            # 分析文本中的信息
            print("�� 分析文本内容...")
            
            # 查找所有包含"小鸡科技"的段落
            paragraphs_with_keyword = []
            if full_page_text:
                lines = full_page_text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if '小鸡科技' in line and len(line) > 10:
                        # 获取上下文
                        context_start = max(0, i-2)
                        context_end = min(len(lines), i+3)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        paragraphs_with_keyword.append({
                            'line_number': i,
                            'content': line,
                            'context': context.strip(),
                            'length': len(line)
                        })
            
            print(f"📊 找到 {len(paragraphs_with_keyword)} 个包含关键词的段落")
            
            # 查找可能的网页来源信息
            print("🔍 查找网页来源信息...")
            
            # 常见的网页来源模式
            source_patterns = [
                r'来源[：:]\s*([^\n]+)',
                r'参考[：:]\s*([^\n]+)',
                r'引用[：:]\s*([^\n]+)',
                r'Source[：:]\s*([^\n]+)',
                r'Reference[：:]\s*([^\n]+)',
                r'根据[：:]?\s*([^\n]*网[^\n]*)',
                r'据[：:]?\s*([^\n]*网[^\n]*)',
                r'摘自[：:]\s*([^\n]+)',
                r'\[[0-9]+\]\s*([^\n]+)',  # 引用标记
                r'(https?://[^\s\)]+)',    # URL
                r'(www\.[^\s\)]+)',        # www链接
            ]
            
            found_sources = []
            if full_page_text:
                for pattern in source_patterns:
                    matches = re.findall(pattern, full_page_text, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            found_sources.append({
                                'pattern': pattern,
                                'source': match.strip(),
                                'type': 'source_reference'
                            })
                        print(f"  模式 '{pattern}' 找到 {len(matches)} 个来源")
            
            # 查找数字引用（如[1], [2]等）
            print("🔍 查找数字引用...")
            citation_pattern = r'\[(\d+)\]'
            citations = re.findall(citation_pattern, full_page_text or '')
            print(f"📊 找到 {len(citations)} 个数字引用: {citations}")
            
            # 分析回复的结构
            print("🔍 分析回复结构...")
            
            # 查找列表项
            list_items = []
            if full_page_text:
                # 查找以数字、字母或符号开头的列表项
                list_patterns = [
                    r'^[0-9]+[.、]\s*(.+)$',     # 数字列表
                    r'^[•·]\s*(.+)$',           # 项目符号
                    r'^-\s*(.+)$',              # 破折号列表
                    r'^[一二三四五六七八九十]+[、.]\s*(.+)$',  # 中文数字
                ]
                
                lines = full_page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if '小鸡科技' in line:
                        for pattern in list_patterns:
                            match = re.match(pattern, line, re.MULTILINE)
                            if match:
                                list_items.append({
                                    'pattern': pattern,
                                    'content': match.group(1),
                                    'full_line': line
                                })
            
            print(f"📊 找到 {len(list_items)} 个列表项")
            
            # 保存所有提取的信息
            extracted_data = {
                'query': '小鸡科技',
                'timestamp': datetime.now().isoformat(),
                'extraction_method': 'complete_content_analysis',
                'total_messages': len(all_messages),
                'messages': all_messages,
                'paragraphs_with_keyword': paragraphs_with_keyword,
                'found_sources': found_sources,
                'citations': citations,
                'list_items': list_items,
                'full_page_length': len(full_page_text) if full_page_text else 0,
                'statistics': {
                    'total_paragraphs': len(paragraphs_with_keyword),
                    'total_sources': len(found_sources),
                    'total_citations': len(citations),
                    'total_list_items': len(list_items)
                }
            }
            
            # 保存到文件
            filename = f"data/deepseek_complete_content_{timestamp}.json"
            os.makedirs("data", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 完整内容已保存到: {filename}")
            print(f"📊 提取统计:")
            print(f"  - 消息数量: {len(all_messages)}")
            print(f"  - 相关段落: {len(paragraphs_with_keyword)}")
            print(f"  - 来源信息: {len(found_sources)}")
            print(f"  - 数字引用: {len(citations)}")
            print(f"  - 列表项: {len(list_items)}")
            print(f"  - 页面总长度: {len(full_page_text) if full_page_text else 0} 字符")
            
            # 显示一些示例内容
            if paragraphs_with_keyword:
                print(f"\n📝 相关段落示例:")
                for i, para in enumerate(paragraphs_with_keyword[:3]):
                    print(f"  {i+1}. {para['content'][:100]}...")
            
            if found_sources:
                print(f"\n🔗 找到的来源示例:")
                for i, source in enumerate(found_sources[:3]):
                    print(f"  {i+1}. {source['source'][:80]}...")
            
            # 保存完整页面截图
            await page.screenshot(path=f"deepseek_complete_{timestamp}.png", full_page=True)
            print(f"📸 已保存完整页面截图")
            
            await page.wait_for_timeout(5000)
            await browser.close()
            print("✅ 完整内容提取完成")
            
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(extract_complete_content())
