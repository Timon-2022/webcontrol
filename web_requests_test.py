#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用requests库测试网页访问
避免浏览器兼容性问题
"""

import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

def test_website_access():
    """测试网站访问"""
    print("=" * 50)
    print("🌐 网站访问测试 (使用requests)")
    print("=" * 50)
    
    # 设置请求头，模拟真实浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # 测试的网站列表
    test_sites = [
        {
            'name': 'DeepSeek',
            'url': 'https://chat.deepseek.com',
            'description': 'DeepSeek AI聊天网站'
        },
        {
            'name': 'Kimi',
            'url': 'https://kimi.moonshot.cn',
            'description': 'Kimi AI聊天网站'
        },
        {
            'name': '百度',
            'url': 'https://www.baidu.com',
            'description': '百度搜索（测试网络连接）'
        }
    ]
    
    results = []
    
    for site in test_sites:
        print(f"\n🔍 测试 {site['name']} ({site['description']})")
        print(f"🌐 URL: {site['url']}")
        
        try:
            # 发送GET请求
            response = requests.get(
                site['url'], 
                headers=headers, 
                timeout=30,
                allow_redirects=True
            )
            
            print(f"✅ 状态码: {response.status_code}")
            print(f"📄 内容长度: {len(response.text)} 字符")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取页面标题
            title = soup.title.string if soup.title else "无标题"
            print(f"📋 页面标题: {title}")
            
            # 查找常见的输入框元素
            input_elements = []
            
            # 查找textarea
            textareas = soup.find_all('textarea')
            if textareas:
                print(f"📝 找到 {len(textareas)} 个textarea元素")
                for i, ta in enumerate(textareas[:3]):  # 只显示前3个
                    placeholder = ta.get('placeholder', '无placeholder')
                    input_elements.append(f"textarea[{i}]: {placeholder}")
            
            # 查找text输入框
            text_inputs = soup.find_all('input', {'type': 'text'})
            if text_inputs:
                print(f"⌨️ 找到 {len(text_inputs)} 个text输入框")
                for i, inp in enumerate(text_inputs[:3]):
                    placeholder = inp.get('placeholder', '无placeholder')
                    input_elements.append(f"input[{i}]: {placeholder}")
            
            # 查找可能的聊天相关元素
            chat_elements = soup.find_all(class_=lambda x: x and ('chat' in x.lower() or 'input' in x.lower()))
            if chat_elements:
                print(f"💬 找到 {len(chat_elements)} 个聊天相关元素")
            
            # 保存结果
            result = {
                'website': site['name'],
                'url': site['url'],
                'status_code': response.status_code,
                'title': title,
                'content_length': len(response.text),
                'input_elements': input_elements,
                'chat_elements_count': len(chat_elements),
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            results.append(result)
            
            # 如果是DeepSeek或Kimi，保存页面内容用于分析
            if site['name'] in ['DeepSeek', 'Kimi']:
                filename = f"data/{site['name'].lower()}_page_content.html"
                os.makedirs("data", exist_ok=True)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"💾 页面内容已保存到: {filename}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            result = {
                'website': site['name'],
                'url': site['url'],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            results.append(result)
        
        except Exception as e:
            print(f"❌ 其他错误: {e}")
            result = {
                'website': site['name'],
                'url': site['url'],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            results.append(result)
    
    # 保存测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/web_access_test_{timestamp}.json"
    
    os.makedirs("data", exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_type': 'web_access_test',
            'timestamp': datetime.now().isoformat(),
            'total_sites': len(test_sites),
            'successful_sites': len([r for r in results if r.get('success', False)]),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 测试结果已保存到: {filename}")
    
    # 显示总结
    print(f"\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    print(f"✅ 成功访问: {len(successful)} 个网站")
    print(f"❌ 访问失败: {len(failed)} 个网站")
    
    if successful:
        print("\n✅ 成功的网站:")
        for result in successful:
            print(f"  - {result['website']}: {result['title']}")
    
    if failed:
        print("\n❌ 失败的网站:")
        for result in failed:
            print(f"  - {result['website']}: {result.get('error', '未知错误')}")
    
    print(f"\n💡 说明:")
    print("- 这种方法可以访问网页内容，但无法模拟用户交互")
    print("- 对于需要登录的AI聊天网站，可能只能看到登录页面")
    print("- 可以分析页面结构，了解网站的基本信息")
    
    return results

def analyze_deepseek_page():
    """分析DeepSeek页面结构"""
    print(f"\n🔍 分析DeepSeek页面结构...")
    
    deepseek_file = "data/deepseek_page_content.html"
    if os.path.exists(deepseek_file):
        with open(deepseek_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        print("📋 页面元素分析:")
        
        # 查找所有可能的输入相关元素
        all_inputs = soup.find_all(['input', 'textarea', 'button'])
        print(f"  - 总输入元素: {len(all_inputs)} 个")
        
        # 查找包含特定关键词的元素
        keywords = ['chat', 'input', 'message', 'send', 'submit']
        for keyword in keywords:
            elements = soup.find_all(class_=lambda x: x and keyword in x.lower())
            if elements:
                print(f"  - 包含'{keyword}'的元素: {len(elements)} 个")
        
        # 查找可能的登录相关元素
        login_keywords = ['login', 'signin', 'auth', '登录', '注册']
        login_elements = []
        for keyword in login_keywords:
            elements = soup.find_all(string=lambda text: text and keyword in text.lower())
            login_elements.extend(elements)
        
        if login_elements:
            print(f"  - 可能需要登录 (找到 {len(login_elements)} 个登录相关文本)")
        
    else:
        print("❌ 未找到DeepSeek页面文件")

if __name__ == "__main__":
    # 执行网站访问测试
    results = test_website_access()
    
    # 分析DeepSeek页面
    analyze_deepseek_page()
    
    print(f"\n" + "=" * 50)
    print("🏁 测试完成")
    print("=" * 50) 