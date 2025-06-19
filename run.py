#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI网站搜索分析工具 - 快速启动脚本
"""

import os
import sys
import subprocess

def check_installation():
    """检查安装状态"""
    try:
        import playwright
        import nltk
        import textblob
        import bs4
        import pandas
        return True
    except ImportError:
        return False

def install_if_needed():
    """如果需要则安装依赖"""
    if not check_installation():
        print("检测到缺少依赖，正在自动安装...")
        try:
            subprocess.run([sys.executable, "setup.py"], check=True)
            return True
        except subprocess.CalledProcessError:
            print("自动安装失败，请手动运行: python setup.py")
            return False
    return True

def main():
    """主函数"""
    print("AI网站搜索分析工具 - 快速启动")
    print("=" * 40)
    
    # 检查安装
    if not install_if_needed():
        sys.exit(1)
    
    # 启动主程序
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main() 