#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级AI网站搜索分析工具 - 主程序
提供完整的菜单系统和功能选择
"""

import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any

from integrated_analyzer import IntegratedAnalyzer
from login_manager import LoginManager


class AdvancedMain:
    """高级主程序类"""
    
    def __init__(self):
        self.analyzer = None
        self.login_manager = LoginManager()
        
    def print_banner(self):
        """打印程序横幅"""
        print("="*80)
        print("               AI网站搜索分析工具 v2.0")
        print("       自动化搜索 + 智能分析 + 数据可视化")
        print("="*80)
        print()
    
    def print_main_menu(self):
        """打印主菜单"""
        print("主菜单:")
        print("1. 单个关键词分析")
        print("2. 批量关键词分析")
        print("3. 查看历史分析结果")
        print("4. 管理登录状态")
        print("5. 系统设置")
        print("6. 帮助信息")
        print("0. 退出程序")
        print("-" * 40)
    
    def print_login_menu(self):
        """打印登录管理菜单"""
        print("\n登录状态管理:")
        print("1. 检查当前登录状态")
        print("2. 手动登录DeepSeek")
        print("3. 删除登录状态")
        print("4. 测试登录状态")
        print("0. 返回主菜单")
        print("-" * 40)
    
    def print_settings_menu(self):
        """打印设置菜单"""
        print("\n系统设置:")
        print("1. 查看当前设置")
        print("2. 设置结果保存目录")
        print("3. 清理临时文件")
        print("4. 查看系统信息")
        print("0. 返回主菜单")
        print("-" * 40)
    
    async def handle_single_analysis(self):
        """处理单个关键词分析"""
        print("\n" + "="*60)
        print("单个关键词分析")
        print("="*60)
        
        # 获取关键词
        keyword = input("请输入要分析的关键词: ").strip()
        if not keyword:
            print("❌ 关键词不能为空")
            return
        
        # 获取详细查询（可选）
        print(f"\n为关键词 '{keyword}' 设置详细查询（可选）:")
        print("示例: 小鸡科技的最新信息，包括公司背景、业务范围、最新动态")
        detailed_query = input("详细查询（直接回车使用默认）: ").strip()
        
        if not detailed_query:
            detailed_query = None
        
        # 确认执行
        print(f"\n将要执行:")
        print(f"关键词: {keyword}")
        print(f"详细查询: {detailed_query or '使用默认模板'}")
        
        confirm = input("\n确认执行？(y/n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        # 执行分析
        try:
            if not self.analyzer:
                self.analyzer = IntegratedAnalyzer()
            
            print("\n开始分析...")
            result = await self.analyzer.search_and_analyze(keyword, detailed_query)
            
            if result:
                print("\n✅ 分析完成！")
                self.print_analysis_result(result)
            else:
                print("\n❌ 分析失败")
                
        except Exception as e:
            print(f"\n❌ 分析过程中出现错误: {e}")
    
    async def handle_batch_analysis(self):
        """处理批量关键词分析"""
        print("\n" + "="*60)
        print("批量关键词分析")
        print("="*60)
        
        # 获取关键词列表
        print("请输入要分析的关键词（每行一个，空行结束）:")
        keywords = []
        while True:
            keyword = input(f"关键词 {len(keywords)+1}: ").strip()
            if not keyword:
                break
            keywords.append(keyword)
        
        if not keywords:
            print("❌ 至少需要输入一个关键词")
            return
        
        # 获取详细查询（可选）
        queries = {}
        print(f"\n为每个关键词设置详细查询（可选）:")
        for keyword in keywords:
            query = input(f"'{keyword}' 的详细查询（直接回车跳过）: ").strip()
            if query:
                queries[keyword] = query
        
        # 确认执行
        print(f"\n将要分析 {len(keywords)} 个关键词:")
        for i, keyword in enumerate(keywords, 1):
            query_info = f" (自定义查询)" if keyword in queries else " (默认查询)"
            print(f"{i}. {keyword}{query_info}")
        
        print(f"\n预计耗时: {len(keywords) * 30} 秒左右")
        confirm = input("确认执行？(y/n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        # 执行批量分析
        try:
            if not self.analyzer:
                self.analyzer = IntegratedAnalyzer()
            
            print("\n开始批量分析...")
            batch_results = await self.analyzer.batch_analyze(keywords, queries if queries else None)
            
            if batch_results:
                print("\n✅ 批量分析完成！")
                
                # 生成比较报告
                comparison_report = self.analyzer.generate_comparison_report(batch_results)
                self.analyzer.print_comparison_summary(comparison_report)
                
                # 保存比较报告
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                comparison_file = f"comparison_report_{len(keywords)}_keywords_{timestamp}.json"
                with open(comparison_file, 'w', encoding='utf-8') as f:
                    json.dump(comparison_report, f, ensure_ascii=False, indent=2)
                print(f"\n比较报告已保存: {comparison_file}")
                
            else:
                print("\n❌ 批量分析失败")
                
        except Exception as e:
            print(f"\n❌ 批量分析过程中出现错误: {e}")
    
    def handle_history_results(self):
        """查看历史分析结果"""
        print("\n" + "="*60)
        print("历史分析结果")
        print("="*60)
        
        # 查找结果目录
        results_dirs = ["analysis_results", "results", "."]
        found_files = []
        
        for results_dir in results_dirs:
            if os.path.exists(results_dir):
                for file in os.listdir(results_dir):
                    if file.endswith('.json') and ('analysis' in file or 'search' in file or 'comparison' in file):
                        file_path = os.path.join(results_dir, file)
                        file_stat = os.stat(file_path)
                        found_files.append({
                            'path': file_path,
                            'name': file,
                            'size': file_stat.st_size,
                            'mtime': datetime.fromtimestamp(file_stat.st_mtime)
                        })
        
        if not found_files:
            print("未找到历史分析结果文件")
            return
        
        # 按修改时间排序
        found_files.sort(key=lambda x: x['mtime'], reverse=True)
        
        print(f"找到 {len(found_files)} 个结果文件:")
        print("-" * 80)
        print(f"{'序号':<4} {'文件名':<40} {'大小':<10} {'修改时间':<20}")
        print("-" * 80)
        
        for i, file_info in enumerate(found_files[:20], 1):  # 只显示最近20个
            size_str = f"{file_info['size']/1024:.1f}KB"
            time_str = file_info['mtime'].strftime('%Y-%m-%d %H:%M')
            print(f"{i:<4} {file_info['name']:<40} {size_str:<10} {time_str:<20}")
        
        if len(found_files) > 20:
            print(f"... 还有 {len(found_files)-20} 个文件")
        
        # 选择查看文件
        try:
            choice = input("\n输入序号查看文件内容（直接回车返回）: ").strip()
            if choice:
                index = int(choice) - 1
                if 0 <= index < min(len(found_files), 20):
                    self.show_result_file(found_files[index]['path'])
                else:
                    print("序号无效")
        except ValueError:
            print("请输入有效的数字")
    
    def show_result_file(self, file_path: str):
        """显示结果文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n文件: {file_path}")
            print("="*60)
            
            # 根据文件类型显示不同内容
            if 'comparison_time' in data:
                # 比较报告
                print("类型: 比较分析报告")
                print(f"比较时间: {data['comparison_time']}")
                print(f"关键词: {', '.join(data['keywords_compared'])}")
                
                if 'rankings' in data and 'by_frequency' in data['rankings']:
                    print("\n频度排名:")
                    for i, (keyword, info) in enumerate(data['rankings']['by_frequency'][:5], 1):
                        print(f"{i}. {keyword}: {info['keyword_frequency']:.2f}%")
                        
            elif 'analysis_time' in data:
                # 分析报告
                print("类型: 关键词分析报告")
                print(f"关键词: {data.get('keyword', 'N/A')}")
                print(f"分析时间: {data['analysis_time']}")
                
                if 'summary' in data:
                    summary = data['summary']
                    print(f"\n分析摘要:")
                    print(f"关键词频度: {summary.get('keyword_frequency', 'N/A')}")
                    print(f"整体情绪: {summary.get('overall_sentiment', 'N/A')}")
                    print(f"权威性等级: {summary.get('authority_level', 'N/A')}")
                    print(f"相关性等级: {summary.get('relevance_level', 'N/A')}")
                    
            elif 'website' in data:
                # 搜索结果
                print("类型: 搜索结果")
                print(f"网站: {data.get('website', 'N/A')}")
                print(f"查询: {data.get('query', 'N/A')}")
                print(f"成功: {data.get('success', 'N/A')}")
                
                if data.get('content'):
                    content = data['content'][:200] + "..." if len(data['content']) > 200 else data['content']
                    print(f"\n内容预览:\n{content}")
                    
            else:
                print("类型: 未知格式")
                print(f"数据键: {list(data.keys())}")
                
        except Exception as e:
            print(f"读取文件失败: {e}")
    
    async def handle_login_management(self):
        """处理登录状态管理"""
        while True:
            self.print_login_menu()
            choice = input("请选择操作: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.login_manager.check_login_state()
            elif choice == '2':
                await self.login_manager.manual_login()
            elif choice == '3':
                self.login_manager.clear_login_state()
            elif choice == '4':
                await self.login_manager.test_login_state()
            else:
                print("无效选择，请重新输入")
            
            input("\n按回车键继续...")
    
    def handle_settings(self):
        """处理系统设置"""
        while True:
            self.print_settings_menu()
            choice = input("请选择操作: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.show_current_settings()
            elif choice == '2':
                self.set_results_directory()
            elif choice == '3':
                self.clean_temp_files()
            elif choice == '4':
                self.show_system_info()
            else:
                print("无效选择，请重新输入")
            
            input("\n按回车键继续...")
    
    def show_current_settings(self):
        """显示当前设置"""
        print("\n当前设置:")
        print(f"工作目录: {os.getcwd()}")
        print(f"登录状态文件: {'存在' if os.path.exists('login_state.json') else '不存在'}")
        print(f"结果目录: analysis_results")
        print(f"Python版本: {os.sys.version}")
    
    def set_results_directory(self):
        """设置结果保存目录"""
        current_dir = "analysis_results"
        print(f"\n当前结果目录: {current_dir}")
        new_dir = input("输入新的结果目录（直接回车保持不变）: ").strip()
        
        if new_dir:
            try:
                os.makedirs(new_dir, exist_ok=True)
                print(f"✅ 结果目录设置为: {new_dir}")
                # 这里可以更新配置文件
            except Exception as e:
                print(f"❌ 设置失败: {e}")
    
    def clean_temp_files(self):
        """清理临时文件"""
        print("\n清理临时文件...")
        
        temp_patterns = ['*.png', '*.log', '*_temp_*']
        cleaned_count = 0
        
        for pattern in temp_patterns:
            import glob
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                    cleaned_count += 1
                    print(f"删除: {file}")
                except Exception as e:
                    print(f"删除失败 {file}: {e}")
        
        print(f"✅ 清理完成，删除了 {cleaned_count} 个文件")
    
    def show_system_info(self):
        """显示系统信息"""
        import platform
        import sys
        
        print("\n系统信息:")
        print(f"操作系统: {platform.system()} {platform.release()}")
        print(f"Python版本: {sys.version}")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"可用内存: {self.get_memory_info()}")
    
    def get_memory_info(self) -> str:
        """获取内存信息"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return f"{memory.available / 1024**3:.1f}GB 可用 / {memory.total / 1024**3:.1f}GB 总计"
        except ImportError:
            return "需要安装 psutil 包才能显示内存信息"
    
    def print_help(self):
        """显示帮助信息"""
        print("\n" + "="*60)
        print("帮助信息")
        print("="*60)
        print("""
功能说明:
1. 单个关键词分析: 对单个关键词进行深度分析，包括频度、情绪、权威性、相关性
2. 批量关键词分析: 同时分析多个关键词，并生成比较报告
3. 历史结果查看: 查看之前的分析结果和报告
4. 登录状态管理: 管理DeepSeek网站的登录状态
5. 系统设置: 配置程序设置和清理文件

使用提示:
- 首次使用前请先进行登录状态管理，手动登录DeepSeek
- 分析过程需要联网，请确保网络连接正常
- 批量分析耗时较长，建议选择合适的关键词数量
- 所有结果都会自动保存在analysis_results目录中

技术支持:
- 如遇到问题，请检查登录状态和网络连接
- 查看生成的日志文件获取详细错误信息
- 确保已安装所有必要的依赖包
        """)
    
    def print_analysis_result(self, result: Dict[str, Any]):
        """打印分析结果摘要"""
        print("\n分析结果:")
        print("-" * 40)
        
        # 搜索结果信息
        search_info = result['search_results']
        print(f"搜索网站: {search_info.get('website', 'N/A')}")
        print(f"搜索成功: {'是' if search_info.get('success') else '否'}")
        
        # 分析摘要
        summary = result['analysis_report']['summary']
        print(f"\n分析摘要:")
        print(f"关键词频度: {summary['keyword_frequency']}")
        print(f"整体情绪: {summary['overall_sentiment']}")
        print(f"权威性等级: {summary['authority_level']}")
        print(f"相关性等级: {summary['relevance_level']}")
        
        # 文件信息
        files = result['files']
        print(f"\n生成文件:")
        print(f"搜索结果: {files['search_file']}")
        print(f"分析报告: {files['report_file']}")
        if files['wordcloud_file']:
            print(f"词云图: {files['wordcloud_file']}")
    
    async def run(self):
        """运行主程序"""
        self.print_banner()
        
        while True:
            try:
                self.print_main_menu()
                choice = input("请选择操作: ").strip()
                
                if choice == '0':
                    print("感谢使用AI网站搜索分析工具！")
                    break
                elif choice == '1':
                    await self.handle_single_analysis()
                elif choice == '2':
                    await self.handle_batch_analysis()
                elif choice == '3':
                    self.handle_history_results()
                elif choice == '4':
                    await self.handle_login_management()
                elif choice == '5':
                    self.handle_settings()
                elif choice == '6':
                    self.print_help()
                else:
                    print("无效选择，请重新输入")
                
                if choice != '0':
                    input("\n按回车键继续...")
                    print()
                    
            except KeyboardInterrupt:
                print("\n\n程序被用户中断，正在退出...")
                break
            except Exception as e:
                print(f"\n程序运行出现错误: {e}")
                input("按回车键继续...")


async def main():
    """主入口函数"""
    app = AdvancedMain()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main()) 