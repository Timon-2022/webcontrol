#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成分析工具 - 结合网页搜索和数据分析功能
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from data_analyzer import DataAnalyzer
from deepseek_web_search import DeepSeekWebSearch


class IntegratedAnalyzer:
    """集成分析器 - 搜索 + 分析"""
    
    def __init__(self, results_dir: str = "analysis_results"):
        """
        初始化集成分析器
        
        Args:
            results_dir: 结果保存目录
        """
        self.results_dir = results_dir
        self.searcher = DeepSeekWebSearch()
        self.analyzer = DataAnalyzer(results_dir=results_dir)
        
        # 创建结果目录
        os.makedirs(results_dir, exist_ok=True)
    
    async def search_and_analyze(self, keyword: str, detailed_query: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        搜索并分析关键词
        
        Args:
            keyword: 关键词
            detailed_query: 详细查询（可选）
            
        Returns:
            分析结果
        """
        print(f"开始搜索和分析关键词: {keyword}")
        
        # 如果没有提供详细查询，使用默认模板
        if not detailed_query:
            detailed_query = f"{keyword}的最新信息，包括公司背景、业务范围、最新动态"
        
        try:
            # 1. 初始化浏览器
            print("正在初始化浏览器...")
            if not await self.searcher.init_browser():
                print("浏览器初始化失败")
                return None
            
            # 2. 执行搜索
            print("正在执行网页搜索...")
            search_results = await self.searcher.chat_with_web_search(detailed_query)
            
            if not search_results or not search_results.get('success'):
                print(f"搜索失败: {search_results.get('error', '未知错误')}")
                return None
            
            # 3. 保存搜索结果
            search_file = os.path.join(self.results_dir, f"search_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(search_file, 'w', encoding='utf-8') as f:
                json.dump(search_results, f, ensure_ascii=False, indent=2)
            print(f"搜索结果已保存: {search_file}")
            
            # 4. 准备分析数据
            analysis_data = [{
                'website': 'DeepSeek',
                'content': search_results.get('content', ''),
                'references': [],  # DeepSeek搜索结果中没有单独的引用信息
                'query': detailed_query,
                'search_time': search_results.get('timestamp', datetime.now().isoformat())
            }]
            
            # 5. 执行数据分析
            print("正在执行数据分析...")
            analysis_report = self.analyzer.generate_comprehensive_report(analysis_data, keyword)
            
            # 6. 保存分析报告
            report_file = os.path.join(self.results_dir, f"analysis_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            self.analyzer.save_report(analysis_report, report_file)
            print(f"分析报告已保存: {report_file}")
            
            # 7. 打印摘要
            self.analyzer.print_summary(analysis_report)
            
            # 8. 返回完整结果
            return {
                'search_results': search_results,
                'analysis_report': analysis_report,
                'files': {
                    'search_file': search_file,
                    'report_file': report_file,
                    'wordcloud_file': analysis_report.get('wordcloud_path')
                }
            }
            
        except Exception as e:
            print(f"搜索和分析过程中出现错误: {e}")
            return None
        finally:
            # 关闭浏览器
            await self.searcher.close_browser()
    
    async def batch_analyze(self, keywords: List[str], queries: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        批量分析多个关键词
        
        Args:
            keywords: 关键词列表
            queries: 关键词对应的详细查询字典
            
        Returns:
            批量分析结果
        """
        print(f"开始批量分析 {len(keywords)} 个关键词")
        
        batch_results = {}
        
        for i, keyword in enumerate(keywords, 1):
            print(f"\n{'='*60}")
            print(f"处理第 {i}/{len(keywords)} 个关键词: {keyword}")
            print(f"{'='*60}")
            
            # 获取对应的详细查询
            detailed_query = queries.get(keyword) if queries else None
            
            # 执行搜索和分析
            result = await self.search_and_analyze(keyword, detailed_query)
            
            if result:
                batch_results[keyword] = result
                print(f"✅ {keyword} 分析完成")
            else:
                print(f"❌ {keyword} 分析失败")
            
            # 短暂延迟，避免请求过于频繁
            if i < len(keywords):
                print("等待 3 秒后处理下一个关键词...")
                await asyncio.sleep(3)
        
        # 保存批量分析结果
        batch_file = os.path.join(self.results_dir, f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(batch_file, 'w', encoding='utf-8') as f:
            # 只保存可序列化的部分
            serializable_results = {}
            for keyword, result in batch_results.items():
                serializable_results[keyword] = {
                    'search_results': result['search_results'],
                    'analysis_summary': result['analysis_report']['summary'],
                    'files': result['files']
                }
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"批量分析完成！结果已保存: {batch_file}")
        print(f"成功分析: {len(batch_results)}/{len(keywords)} 个关键词")
        print(f"{'='*60}")
        
        return batch_results
    
    def generate_comparison_report(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成比较报告
        
        Args:
            batch_results: 批量分析结果
            
        Returns:
            比较报告
        """
        comparison_data = {}
        
        for keyword, result in batch_results.items():
            if result and 'analysis_report' in result:
                summary = result['analysis_report']['summary']
                comparison_data[keyword] = {
                    'keyword_frequency': float(summary['keyword_frequency'].replace('%', '')),
                    'sentiment': summary['overall_sentiment'],
                    'authority': summary['authority_level'],
                    'relevance': summary['relevance_level']
                }
        
        # 创建比较报告
        report = {
            'comparison_time': datetime.now().isoformat(),
            'keywords_compared': list(comparison_data.keys()),
            'comparison_data': comparison_data,
            'rankings': {
                'by_frequency': sorted(comparison_data.items(), key=lambda x: x[1]['keyword_frequency'], reverse=True),
                'by_sentiment': self._group_by_sentiment(comparison_data),
                'by_authority': self._group_by_authority(comparison_data),
                'by_relevance': self._group_by_relevance(comparison_data)
            }
        }
        
        return report
    
    def _group_by_sentiment(self, data: Dict[str, Dict]) -> Dict[str, List[str]]:
        """按情绪分组"""
        groups = {'积极': [], '中性': [], '消极': []}
        for keyword, info in data.items():
            sentiment = info['sentiment']
            if sentiment in groups:
                groups[sentiment].append(keyword)
        return groups
    
    def _group_by_authority(self, data: Dict[str, Dict]) -> Dict[str, List[str]]:
        """按权威性分组"""
        groups = {'高权威性': [], '中等权威性': [], '一般权威性': []}
        for keyword, info in data.items():
            authority = info['authority']
            if authority in groups:
                groups[authority].append(keyword)
        return groups
    
    def _group_by_relevance(self, data: Dict[str, Dict]) -> Dict[str, List[str]]:
        """按相关性分组"""
        groups = {'高相关性': [], '中等相关性': [], '低相关性': []}
        for keyword, info in data.items():
            relevance = info['relevance']
            if relevance in groups:
                groups[relevance].append(keyword)
        return groups
    
    def print_comparison_summary(self, comparison_report: Dict[str, Any]):
        """打印比较摘要"""
        print(f"\n{'='*80}")
        print(f"关键词比较分析报告")
        print(f"{'='*80}")
        print(f"比较时间: {comparison_report['comparison_time']}")
        print(f"比较关键词: {', '.join(comparison_report['keywords_compared'])}")
        
        print(f"\n{'='*80}")
        print("频度排名 (按关键词出现频率):")
        print(f"{'='*80}")
        for i, (keyword, data) in enumerate(comparison_report['rankings']['by_frequency'], 1):
            print(f"{i}. {keyword}: {data['keyword_frequency']:.2f}%")
        
        print(f"\n{'='*80}")
        print("情绪分布:")
        print(f"{'='*80}")
        for sentiment, keywords in comparison_report['rankings']['by_sentiment'].items():
            if keywords:
                print(f"{sentiment}: {', '.join(keywords)}")
        
        print(f"\n{'='*80}")
        print("权威性分布:")
        print(f"{'='*80}")
        for authority, keywords in comparison_report['rankings']['by_authority'].items():
            if keywords:
                print(f"{authority}: {', '.join(keywords)}")
        
        print(f"\n{'='*80}")
        print("相关性分布:")
        print(f"{'='*80}")
        for relevance, keywords in comparison_report['rankings']['by_relevance'].items():
            if keywords:
                print(f"{relevance}: {', '.join(keywords)}")


async def main():
    """主函数 - 演示集成分析功能"""
    print("集成分析工具演示")
    print("="*60)
    
    # 创建集成分析器
    analyzer = IntegratedAnalyzer()
    
    # 单个关键词分析
    print("1. 单个关键词分析演示")
    result = await analyzer.search_and_analyze("小鸡科技")
    
    if result:
        print("✅ 单个关键词分析完成")
    else:
        print("❌ 单个关键词分析失败")
    
    # 批量关键词分析（示例）
    # keywords = ["小鸡科技", "游戏外设", "手柄"]
    # queries = {
    #     "小鸡科技": "小鸡科技的最新信息，包括公司背景、业务范围、最新动态",
    #     "游戏外设": "游戏外设行业的发展趋势和主要厂商",
    #     "手柄": "游戏手柄的技术发展和市场情况"
    # }
    # 
    # print("\n2. 批量关键词分析演示")
    # batch_results = await analyzer.batch_analyze(keywords, queries)
    # 
    # if batch_results:
    #     # 生成比较报告
    #     comparison_report = analyzer.generate_comparison_report(batch_results)
    #     analyzer.print_comparison_summary(comparison_report)


if __name__ == "__main__":
    asyncio.run(main()) 