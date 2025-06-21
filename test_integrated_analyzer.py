#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试集成分析功能
"""

import asyncio
import os
from integrated_analyzer import IntegratedAnalyzer


async def test_single_keyword():
    """测试单个关键词分析"""
    print("="*60)
    print("测试单个关键词分析功能")
    print("="*60)
    
    analyzer = IntegratedAnalyzer()
    
    # 测试单个关键词
    keyword = "小鸡科技"
    print(f"正在分析关键词: {keyword}")
    
    result = await analyzer.search_and_analyze(keyword)
    
    if result:
        print("✅ 单个关键词分析成功！")
        print(f"搜索结果文件: {result['files']['search_file']}")
        print(f"分析报告文件: {result['files']['report_file']}")
        if result['files']['wordcloud_file']:
            print(f"词云图文件: {result['files']['wordcloud_file']}")
        
        # 显示分析摘要
        summary = result['analysis_report']['summary']
        print(f"\n分析摘要:")
        print(f"关键词频度: {summary['keyword_frequency']}")
        print(f"整体情绪: {summary['overall_sentiment']}")
        print(f"权威性等级: {summary['authority_level']}")
        print(f"相关性等级: {summary['relevance_level']}")
        
    else:
        print("❌ 单个关键词分析失败")
    
    return result


async def test_batch_keywords():
    """测试批量关键词分析"""
    print("\n"+"="*60)
    print("测试批量关键词分析功能")
    print("="*60)
    
    analyzer = IntegratedAnalyzer()
    
    # 定义测试关键词
    keywords = ["小鸡科技", "游戏外设"]
    queries = {
        "小鸡科技": "小鸡科技的最新信息，包括公司背景、业务范围、最新动态",
        "游戏外设": "游戏外设行业的发展趋势和主要厂商"
    }
    
    print(f"正在批量分析关键词: {', '.join(keywords)}")
    
    batch_results = await analyzer.batch_analyze(keywords, queries)
    
    if batch_results:
        print("✅ 批量关键词分析成功！")
        
        # 生成比较报告
        comparison_report = analyzer.generate_comparison_report(batch_results)
        analyzer.print_comparison_summary(comparison_report)
        
        # 保存比较报告
        comparison_file = f"comparison_report_{len(keywords)}_keywords.json"
        import json
        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, ensure_ascii=False, indent=2)
        print(f"\n比较报告已保存: {comparison_file}")
        
    else:
        print("❌ 批量关键词分析失败")
    
    return batch_results


async def main():
    """主测试函数"""
    print("集成分析工具测试")
    print("="*60)
    
    # 检查登录状态文件
    if not os.path.exists("login_state.json"):
        print("⚠️  警告: 未找到登录状态文件 login_state.json")
        print("   请先运行 login_manager.py 进行手动登录")
        print("   或者确保已经登录 DeepSeek")
        print()
    
    try:
        # 测试1: 单个关键词分析
        result1 = await test_single_keyword()
        
        # 如果单个测试成功，再进行批量测试
        if result1:
            # 测试2: 批量关键词分析（可选，耗时较长）
            user_input = input("\n是否继续进行批量分析测试？(y/n): ").strip().lower()
            if user_input == 'y':
                await test_batch_keywords()
            else:
                print("跳过批量分析测试")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main()) 