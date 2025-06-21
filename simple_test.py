#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试脚本 - 测试AI网站搜索分析工具的基本功能
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def test_browser():
    """测试浏览器基本功能"""
    print("🔍 测试浏览器启动...")
    
    try:
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            
            # 创建页面
            page = await browser.new_page()
            
            # 访问测试网站
            await page.goto('https://www.google.com', timeout=30000)
            title = await page.title()
            
            print(f"✅ 浏览器测试成功！页面标题: {title}")
            
            # 关闭浏览器
            await browser.close()
            
            return True
            
    except Exception as e:
        print(f"❌ 浏览器测试失败: {e}")
        return False

def test_imports():
    """测试模块导入"""
    print("📦 测试模块导入...")
    
    try:
        # 测试基本模块
        import playwright
        print("✅ Playwright 导入成功")
        
        import requests
        print("✅ Requests 导入成功")
        
        import pandas as pd
        print("✅ Pandas 导入成功")
        
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup 导入成功")
        
        import nltk
        print("✅ NLTK 导入成功")
        
        # 测试项目模块
        from config import AI_WEBSITES, SEARCH_CONFIG, DATA_CONFIG
        print(f"✅ 配置文件导入成功，共配置 {len(AI_WEBSITES)} 个网站")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("⚙️  测试配置文件...")
    
    try:
        from config import AI_WEBSITES, SEARCH_CONFIG, DATA_CONFIG
        
        # 检查网站配置
        if not AI_WEBSITES:
            print("❌ AI_WEBSITES 配置为空")
            return False
            
        print(f"✅ 配置了 {len(AI_WEBSITES)} 个AI网站")
        
        # 显示前5个网站
        for i, site in enumerate(AI_WEBSITES[:5]):
            print(f"   {i+1}. {site['name']} - {site['url']}")
        
        # 检查搜索配置
        required_keys = ['timeout', 'wait_time', 'max_results_per_site', 'retry_count']
        for key in required_keys:
            if key not in SEARCH_CONFIG:
                print(f"❌ SEARCH_CONFIG 缺少 {key} 配置")
                return False
                
        print("✅ 搜索配置检查通过")
        
        # 检查数据配置
        if 'output_dir' not in DATA_CONFIG:
            print("❌ DATA_CONFIG 缺少 output_dir 配置")
            return False
            
        print("✅ 数据配置检查通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置文件测试失败: {e}")
        return False

def test_data_directory():
    """测试数据目录"""
    print("📁 测试数据目录...")
    
    try:
        from config import DATA_CONFIG
        
        output_dir = DATA_CONFIG['output_dir']
        
        # 创建目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)
        
        # 检查目录是否可写
        test_file = os.path.join(output_dir, 'test.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('测试文件')
            
        # 删除测试文件
        os.remove(test_file)
        
        print(f"✅ 数据目录测试通过: {output_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 数据目录测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("🚀 AI网站搜索分析工具 - 简单测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置文件", test_config),
        ("数据目录", test_data_directory),
        ("浏览器功能", test_browser)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
        print("💡 可以运行 'python3 main.py' 开始使用")
    else:
        print("⚠️  部分测试失败，请检查配置")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
