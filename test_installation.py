#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import importlib
import os

def test_import(module_name, description):
    """测试模块导入"""
    try:
        importlib.import_module(module_name)
        print(f"✓ {description} - 导入成功")
        return True
    except ImportError as e:
        print(f"✗ {description} - 导入失败: {e}")
        return False

def test_playwright():
    """测试Playwright安装"""
    try:
        from playwright.async_api import async_playwright
        print("✓ Playwright - 导入成功")
        return True
    except ImportError as e:
        print(f"✗ Playwright - 导入失败: {e}")
        return False

def test_nltk_data():
    """测试NLTK数据"""
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        print("✓ NLTK数据 - 检查通过")
        return True
    except LookupError as e:
        print(f"✗ NLTK数据 - 缺失: {e}")
        print("  请运行: python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords')\"")
        return False

def test_config_files():
    """测试配置文件"""
    required_files = ['config.py', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} - 存在")
        else:
            print(f"✗ {file} - 缺失")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_data_directory():
    """测试数据目录"""
    if os.path.exists('data'):
        print("✓ data目录 - 存在")
        return True
    else:
        print("✗ data目录 - 缺失")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("AI网站搜索分析工具 - 安装测试")
    print("=" * 50)
    
    tests = [
        ("playwright", test_playwright),
        ("nltk", lambda: test_import("nltk", "NLTK")),
        ("textblob", lambda: test_import("textblob", "TextBlob")),
        ("beautifulsoup4", lambda: test_import("bs4", "BeautifulSoup")),
        ("pandas", lambda: test_import("pandas", "Pandas")),
        ("requests", lambda: test_import("requests", "Requests")),
        ("nltk_data", test_nltk_data),
        ("config_files", test_config_files),
        ("data_directory", test_data_directory),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！安装成功。")
        print("可以开始使用: python main.py")
    else:
        print("✗ 部分测试失败，请检查安装。")
        print("建议运行: python setup.py")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 