#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI网站搜索分析工具 - 使用示例
演示如何使用各个模块进行搜索和分析
"""

import asyncio
import json
from web_scraper import WebScraper
from ai_analyzer import AIAnalyzer

async def example_search():
    """示例：搜索特定关键词"""
    print("=== 搜索示例 ===")
    
    # 创建搜索器
    scraper = WebScraper()
    
    # 搜索关键词
    query = "machine learning"
    print(f"搜索关键词: {query}")
    
    # 执行搜索（这里只搜索前3个网站作为示例）
    results = []
    try:
        await scraper.init_browser()
        
        # 只搜索前3个网站作为示例
        from config import AI_WEBSITES
        sample_websites = AI_WEBSITES[:3]
        
        for website in sample_websites:
            print(f"正在搜索 {website['name']}...")
            site_results = await scraper.search_website(website, query)
            results.extend(site_results)
            await asyncio.sleep(1)  # 避免过快请求
            
    except Exception as e:
        print(f"搜索过程中出错: {e}")
    finally:
        await scraper.close_browser()
    
    print(f"搜索完成，获得 {len(results)} 个结果")
    return results

def example_analysis(results, query):
    """示例：分析搜索结果"""
    print("\n=== 分析示例 ===")
    
    # 创建分析器
    analyzer = AIAnalyzer()
    
    # 分析结果
    analysis_results = analyzer.analyze_results(results, query)
    
    # 显示分析摘要
    print(f"查询关键词: {analysis_results['query']}")
    print(f"总结果数: {analysis_results['total_results']}")
    print(f"分析网站数: {analysis_results['websites_analyzed']}")
    
    # 显示关键词频度
    freq_analysis = analysis_results['frequency_analysis']
    print(f"关键词总出现次数: {freq_analysis['total_occurrences']}")
    
    # 显示相关性最高的结果
    print("\n相关性最高的结果:")
    for i, result in enumerate(analysis_results['detailed_analysis'][:3], 1):
        print(f"{i}. {result['website']} - {result['title'][:50]}...")
        print(f"   相关性: {result['relevance_score']:.2f}")
        print(f"   情绪: {result['sentiment']['label']}")
        print(f"   权威性: {result['authority_score']:.2f}")
        print(f"   综合评分: {result['overall_score']:.2f}")
        print()
    
    return analysis_results

def example_custom_analysis():
    """示例：自定义分析"""
    print("\n=== 自定义分析示例 ===")
    
    # 模拟搜索结果数据
    sample_results = [
        {
            'website': 'OpenAI',
            'title': 'Introduction to Machine Learning',
            'content': 'Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience.',
            'link': 'https://openai.com/ml-intro',
            'rank': 1
        },
        {
            'website': 'Google AI',
            'title': 'Deep Learning Fundamentals',
            'content': 'Deep learning uses neural networks with multiple layers to model complex patterns in data.',
            'link': 'https://ai.google/deep-learning',
            'rank': 2
        }
    ]
    
    # 分析
    analyzer = AIAnalyzer()
    analysis = analyzer.analyze_results(sample_results, "machine learning")
    
    print("自定义分析结果:")
    for result in analysis['detailed_analysis']:
        print(f"网站: {result['website']}")
        print(f"标题: {result['title']}")
        print(f"相关性: {result['relevance_score']:.2f}")
        print(f"情绪: {result['sentiment']['label']} (极性: {result['sentiment']['polarity']:.2f})")
        print(f"权威性: {result['authority_score']:.2f}")
        print(f"综合评分: {result['overall_score']:.2f}")
        print("-" * 40)

async def main():
    """主示例函数"""
    print("AI网站搜索分析工具 - 使用示例")
    print("=" * 50)
    
    try:
        # 示例1: 搜索
        results = await example_search()
        
        if results:
            # 示例2: 分析
            analysis = example_analysis(results, "machine learning")
            
            # 示例3: 自定义分析
            example_custom_analysis()
            
            print("\n示例执行完成！")
            print("您可以查看生成的数据文件了解详细结果。")
        else:
            print("未获得搜索结果，跳过分析步骤")
            
    except Exception as e:
        print(f"示例执行出错: {e}")
        print("请确保已正确安装所有依赖")

if __name__ == "__main__":
    asyncio.run(main()) 