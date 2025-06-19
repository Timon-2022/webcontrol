#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """运行命令并显示进度"""
    print(f"正在{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description}完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description}失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ 需要Python 3.8或更高版本")
        print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装Python依赖"""
    # 尝试使用pip3，如果失败则尝试pip
    commands = ["pip3 install -r requirements.txt", "pip install -r requirements.txt"]
    
    for command in commands:
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"✓ 安装Python依赖包完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"尝试命令失败: {command}")
            continue
    
    print("✗ 所有pip命令都失败了")
    return False

def install_playwright():
    """安装Playwright浏览器"""
    # 尝试使用pip3，如果失败则尝试pip
    commands = ["pip3 install playwright", "pip install playwright"]
    
    for command in commands:
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            break
        except subprocess.CalledProcessError:
            continue
    
    return run_command("playwright install chromium", "安装Playwright浏览器")

def create_data_directory():
    """创建数据目录"""
    try:
        os.makedirs("data", exist_ok=True)
        print("✓ 数据目录创建完成")
        return True
    except Exception as e:
        print(f"✗ 创建数据目录失败: {e}")
        return False

def setup_environment():
    """设置环境变量文件"""
    env_file = ".env"
    if not os.path.exists(env_file):
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# AI网站搜索分析工具环境配置\n")
                f.write("# 如需使用OpenAI API，请取消注释并填入您的API密钥\n")
                f.write("# OPENAI_API_KEY=your_openai_api_key_here\n")
            print("✓ 环境配置文件创建完成")
            return True
        except Exception as e:
            print(f"✗ 创建环境配置文件失败: {e}")
            return False
    else:
        print("✓ 环境配置文件已存在")
        return True

def main():
    """主安装函数"""
    print("=" * 50)
    print("AI网站搜索分析工具 - 安装程序")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        print("安装依赖失败，请检查网络连接或手动安装")
        sys.exit(1)
    
    # 安装Playwright
    if not install_playwright():
        print("安装Playwright失败，请手动运行: playwright install chromium")
        sys.exit(1)
    
    # 创建数据目录
    if not create_data_directory():
        print("创建数据目录失败")
        sys.exit(1)
    
    # 设置环境变量
    if not setup_environment():
        print("设置环境变量失败")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("安装完成！")
    print("=" * 50)
    print("使用方法:")
    print("1. 运行主程序: python3 main.py")
    print("2. 仅搜索: python3 web_scraper.py")
    print("3. 仅分析: python3 ai_analyzer.py")
    print("\n注意事项:")
    print("- 首次运行可能需要较长时间")
    print("- 某些网站可能需要VPN访问")
    print("- 建议在config.py中调整搜索参数")
    print("=" * 50)

if __name__ == "__main__":
    main() 