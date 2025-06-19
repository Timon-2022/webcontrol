#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
from datetime import datetime

from web_scraper import WebScraper
from ai_analyzer import AIAnalyzer
from config import DATA_CONFIG

def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    AI网站搜索分析工具                          ║
║                                                              ║
║  功能：                                                      ║
║  1. 自动访问20个AI网站并搜索关键词                           ║
║  2. 提取搜索结果并保存到本地                                 ║
║  3. AI分析关键词频度、相关性、情绪和权威性                   ║
║  4. 生成详细的分析报告                                       ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    """打印菜单选项"""
    menu = """
请选择操作：

1. 执行完整流程（搜索 + 分析）
2. 仅执行网页搜索
3. 仅执行结果分析
4. 查看历史结果
5. 退出

请输入选项 (1-5): """
    return input(menu).strip()

async def run_full_process():
    """执行完整的搜索和分析流程"""
    print("\n=== 开始执行完整流程 ===")
    
    # 获取搜索关键词
    query = input("请输入要搜索的关键词: ").strip()
    if not query:
        print("关键词不能为空！")
        return
    
    print(f"\n开始搜索关键词: {query}")
    print("正在访问20个AI网站...")
    
    # 执行网页搜索
    scraper = WebScraper()
    results = await scraper.scrape_all_websites(query)
    
    if not results:
        print("未获取到任何搜索结果，流程终止")
        return
    
    # 保存搜索结果
    search_file = scraper.save_results(results, query)
    print(f"搜索完成！共获取到 {len(results)} 个结果")
    print(f"搜索结果已保存到: {search_file}")
    
    # 执行AI分析
    print("\n开始AI分析...")
    analyzer = AIAnalyzer()
    analysis_results = analyzer.analyze_results(results, query)
    
    # 保存分析结果
    analysis_file, summary_file = analyzer.save_analysis(analysis_results, query)
    
    print("分析完成！")
    print(f"分析结果已保存到: {analysis_file}")
    print(f"摘要报告已保存到: {summary_file}")
    
    # 显示摘要报告
    print("\n" + "="*50)
    print("摘要报告:")
    print("="*50)
    with open(summary_file, 'r', encoding='utf-8') as f:
        print(f.read())

async def run_search_only():
    """仅执行网页搜索"""
    print("\n=== 仅执行网页搜索 ===")
    
    query = input("请输入要搜索的关键词: ").strip()
    if not query:
        print("关键词不能为空！")
        return
    
    print(f"开始搜索关键词: {query}")
    print("正在访问20个AI网站...")
    
    scraper = WebScraper()
    results = await scraper.scrape_all_websites(query)
    
    if results:
        filename = scraper.save_results(results, query)
        print(f"搜索完成！共获取到 {len(results)} 个结果")
        print(f"结果已保存到: {filename}")
    else:
        print("未获取到任何搜索结果")

def run_analysis_only():
    """仅执行结果分析"""
    print("\n=== 仅执行结果分析 ===")
    
    # 检查是否有搜索结果文件
    data_dir = DATA_CONFIG['output_dir']
    if not os.path.exists(data_dir):
        print("数据目录不存在，请先执行搜索")
        return
    
    # 查找搜索结果文件
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and 'search_results' in f]
    if not json_files:
        print("未找到搜索结果文件，请先执行搜索")
        return
    
    # 显示可用的搜索结果文件
    print("可用的搜索结果文件:")
    for i, file in enumerate(json_files, 1):
        file_path = os.path.join(data_dir, file)
        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
        print(f"{i}. {file} (创建时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # 选择文件
    try:
        choice = int(input(f"\n请选择要分析的文件 (1-{len(json_files)}): ")) - 1
        if choice < 0 or choice >= len(json_files):
            print("无效的选择")
            return
        
        selected_file = json_files[choice]
        file_path = os.path.join(data_dir, selected_file)
        
        print(f"正在分析文件: {selected_file}")
        
        # 执行分析
        analyzer = AIAnalyzer()
        search_data = analyzer.load_search_results(file_path)
        
        if not search_data:
            print("加载搜索结果失败")
            return
        
        analysis_results = analyzer.analyze_results(search_data['results'], search_data['query'])
        analysis_file, summary_file = analyzer.save_analysis(analysis_results, search_data['query'])
        
        print("分析完成！")
        print(f"分析结果已保存到: {analysis_file}")
        print(f"摘要报告已保存到: {summary_file}")
        
        # 显示摘要报告
        print("\n" + "="*50)
        print("摘要报告:")
        print("="*50)
        with open(summary_file, 'r', encoding='utf-8') as f:
            print(f.read())
            
    except ValueError:
        print("请输入有效的数字")
    except Exception as e:
        print(f"分析过程中出错: {e}")

def view_history():
    """查看历史结果"""
    print("\n=== 查看历史结果 ===")
    
    data_dir = DATA_CONFIG['output_dir']
    if not os.path.exists(data_dir):
        print("数据目录不存在")
        return
    
    # 查找所有结果文件
    search_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and 'search_results' in f]
    analysis_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and 'analysis_results' in f]
    summary_files = [f for f in os.listdir(data_dir) if f.endswith('.txt') and 'summary_report' in f]
    
    print(f"搜索结果文件: {len(search_files)} 个")
    print(f"分析结果文件: {len(analysis_files)} 个")
    print(f"摘要报告文件: {len(summary_files)} 个")
    
    if search_files:
        print("\n最新的搜索结果:")
        latest_search = max(search_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
        file_path = os.path.join(data_dir, latest_search)
        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
        print(f"  {latest_search} (创建时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    if summary_files:
        print("\n最新的摘要报告:")
        latest_summary = max(summary_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
        file_path = os.path.join(data_dir, latest_summary)
        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
        print(f"  {latest_summary} (创建时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # 显示最新摘要报告的内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\n摘要报告内容:")
                print("="*50)
                print(content)
        except Exception as e:
            print(f"读取摘要报告失败: {e}")

async def main():
    """主函数"""
    print_banner()
    
    while True:
        try:
            choice = print_menu()
            
            if choice == '1':
                await run_full_process()
            elif choice == '2':
                await run_search_only()
            elif choice == '3':
                run_analysis_only()
            elif choice == '4':
                view_history()
            elif choice == '5':
                print("感谢使用！再见！")
                break
            else:
                print("无效的选择，请重新输入")
            
            input("\n按回车键继续...")
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"程序执行出错: {e}")
            input("按回车键继续...")

if __name__ == "__main__":
    asyncio.run(main()) 