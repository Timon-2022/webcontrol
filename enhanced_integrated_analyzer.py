#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版集成分析工具 - 包含网页源URL提取功能
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from data_analyzer import DataAnalyzer
from deepseek_web_sources_extractor import DeepSeekWebSourcesExtractor


class EnhancedIntegratedAnalyzer:
    """增强版集成分析器 - 搜索 + 源提取 + 分析"""
    
    def __init__(self, results_dir: str = "enhanced_analysis_results"):
        """
        初始化增强版集成分析器
        
        Args:
            results_dir: 结果保存目录
        """
        self.results_dir = results_dir
        self.sources_extractor = DeepSeekWebSourcesExtractor()
        self.analyzer = DataAnalyzer(results_dir=results_dir)
        
        # 创建结果目录
        os.makedirs(results_dir, exist_ok=True)
    
    async def search_analyze_and_extract_sources(self, keyword: str, detailed_query: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        搜索、分析并提取网页源
        
        Args:
            keyword: 关键词
            detailed_query: 详细查询（可选）
            
        Returns:
            完整分析结果，包含网页源URL
        """
        print(f"开始增强版搜索和分析关键词: {keyword}")
        
        # 如果没有提供详细查询，使用默认模板
        if not detailed_query:
            detailed_query = f"{keyword}的最新信息，包括公司背景、业务范围、最新动态"
        
        try:
            # 1. 初始化浏览器
            print("正在初始化浏览器...")
            if not await self.sources_extractor.init_browser():
                print("浏览器初始化失败")
                return None
            
            # 2. 执行搜索并提取源
            print("正在执行网页搜索和源提取...")
            search_results = await self.sources_extractor.search_and_extract_sources(detailed_query)
            
            if not search_results or not search_results.get('success'):
                print(f"搜索失败: {search_results.get('error', '未知错误')}")
                return None
            
            # 3. 保存搜索结果（包含源URL）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            search_file = os.path.join(self.results_dir, f"enhanced_search_{keyword}_{timestamp}.json")
            with open(search_file, 'w', encoding='utf-8') as f:
                json.dump(search_results, f, ensure_ascii=False, indent=2)
            print(f"搜索结果已保存: {search_file}")
            
            # 4. 准备分析数据
            analysis_data = [{
                'website': 'DeepSeek',
                'content': search_results.get('content', ''),
                'references': search_results.get('sources_urls', []),  # 使用提取的源URL作为引用
                'query': detailed_query,
                'search_time': search_results.get('timestamp', datetime.now().isoformat()),
                'sources_count': search_results.get('sources_count', 0)
            }]
            
            # 5. 执行数据分析
            print("正在执行数据分析...")
            analysis_report = self.analyzer.generate_comprehensive_report(analysis_data, keyword)
            
            # 6. 增强分析报告，添加源URL信息
            analysis_report['sources_info'] = {
                'sources_count': search_results.get('sources_count', 0),
                'extracted_urls_count': len(search_results.get('sources_urls', [])),
                'sources_urls': search_results.get('sources_urls', [])
            }
            
            # 7. 保存增强分析报告
            report_file = os.path.join(self.results_dir, f"enhanced_analysis_{keyword}_{timestamp}.json")
            self.analyzer.save_report(analysis_report, report_file)
            print(f"增强分析报告已保存: {report_file}")
            
            # 8. 打印增强摘要
            self.print_enhanced_summary(analysis_report, search_results)
            
            # 9. 返回完整结果
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
            print(f"增强搜索和分析过程中出现错误: {e}")
            return None
        finally:
            # 关闭浏览器
            await self.sources_extractor.close_browser()
    
    def print_enhanced_summary(self, analysis_report: Dict[str, Any], search_results: Dict[str, Any]):
        """打印增强版分析摘要"""
        print(f"\n{'='*80}")
        print(f"增强版关键词分析报告: {analysis_report['keyword']}")
        print(f"{'='*80}")
        print(f"分析时间: {analysis_report['analysis_time']}")
        print(f"数据源数量: {analysis_report['total_sources']}")
        print(f"文本数量: {analysis_report['total_texts']}")
        
        # 网页源信息
        sources_info = analysis_report.get('sources_info', {})
        print(f"\n{'='*80}")
        print("网页源信息:")
        print(f"{'='*80}")
        print(f"搜索到网页数: {sources_info.get('sources_count', 0)}")
        print(f"成功提取URL数: {sources_info.get('extracted_urls_count', 0)}")
        
        # 显示前几个URL
        sources_urls = sources_info.get('sources_urls', [])
        if sources_urls:
            print(f"\n主要网页源:")
            for i, source in enumerate(sources_urls[:5], 1):
                if isinstance(source, dict):
                    title = source.get('title', 'N/A')[:60]
                    url = source.get('url', 'N/A')
                    print(f"{i}. {title}...")
                    print(f"   {url}")
                else:
                    print(f"{i}. {source}")
            
            if len(sources_urls) > 5:
                print(f"... 还有 {len(sources_urls) - 5} 个网页源")
        
        print(f"\n{'='*80}")
        print("分析结果摘要:")
        print(f"{'='*80}")
        summary = analysis_report['summary']
        print(f"关键词频度: {summary['keyword_frequency']}")
        print(f"整体情绪: {summary['overall_sentiment']}")
        print(f"权威性等级: {summary['authority_level']}")
        print(f"相关性等级: {summary['relevance_level']}")
        print(f"{'='*80}")
    
    async def batch_enhanced_analyze(self, keywords: List[str], queries: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        批量增强分析多个关键词
        
        Args:
            keywords: 关键词列表
            queries: 关键词对应的详细查询字典
            
        Returns:
            批量分析结果
        """
        print(f"开始批量增强分析 {len(keywords)} 个关键词")
        
        batch_results = {}
        
        for i, keyword in enumerate(keywords, 1):
            print(f"\n{'='*80}")
            print(f"处理第 {i}/{len(keywords)} 个关键词: {keyword}")
            print(f"{'='*80}")
            
            # 获取对应的详细查询
            detailed_query = queries.get(keyword) if queries else None
            
            # 执行增强搜索和分析
            result = await self.search_analyze_and_extract_sources(keyword, detailed_query)
            
            if result:
                batch_results[keyword] = result
                print(f"✅ {keyword} 增强分析完成")
                
                # 显示本次分析的源URL数量
                sources_count = result['search_results'].get('sources_count', 0)
                extracted_count = len(result['search_results'].get('sources_urls', []))
                print(f"   搜索到网页: {sources_count} 个")
                print(f"   提取URL: {extracted_count} 个")
            else:
                print(f"❌ {keyword} 增强分析失败")
            
            # 短暂延迟，避免请求过于频繁
            if i < len(keywords):
                print("等待 5 秒后处理下一个关键词...")
                await asyncio.sleep(5)
        
        # 保存批量分析结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_file = os.path.join(self.results_dir, f"enhanced_batch_analysis_{timestamp}.json")
        with open(batch_file, 'w', encoding='utf-8') as f:
            # 只保存可序列化的部分
            serializable_results = {}
            for keyword, result in batch_results.items():
                serializable_results[keyword] = {
                    'search_results': result['search_results'],
                    'analysis_summary': result['analysis_report']['summary'],
                    'sources_info': result['analysis_report'].get('sources_info', {}),
                    'files': result['files']
                }
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*80}")
        print(f"批量增强分析完成！结果已保存: {batch_file}")
        print(f"成功分析: {len(batch_results)}/{len(keywords)} 个关键词")
        
        # 显示总体统计
        total_sources = sum(r['search_results'].get('sources_count', 0) for r in batch_results.values())
        total_extracted = sum(len(r['search_results'].get('sources_urls', [])) for r in batch_results.values())
        print(f"总搜索网页数: {total_sources}")
        print(f"总提取URL数: {total_extracted}")
        print(f"{'='*80}")
        
        return batch_results
    
    def generate_sources_summary_report(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成网页源汇总报告
        
        Args:
            batch_results: 批量分析结果
            
        Returns:
            网页源汇总报告
        """
        all_sources = []
        keyword_sources = {}
        
        for keyword, result in batch_results.items():
            sources_urls = result['search_results'].get('sources_urls', [])
            keyword_sources[keyword] = {
                'sources_count': result['search_results'].get('sources_count', 0),
                'extracted_count': len(sources_urls),
                'urls': sources_urls
            }
            
            # 收集所有源URL
            for source in sources_urls:
                if isinstance(source, dict):
                    all_sources.append({
                        'keyword': keyword,
                        'url': source.get('url', ''),
                        'title': source.get('title', ''),
                        'selector': source.get('selector', '')
                    })
        
        # 统计域名分布
        domain_stats = {}
        for source in all_sources:
            url = source['url']
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domain_stats[domain] = domain_stats.get(domain, 0) + 1
                except:
                    continue
        
        # 生成汇总报告
        report = {
            'summary_time': datetime.now().isoformat(),
            'keywords_analyzed': list(keyword_sources.keys()),
            'total_keywords': len(keyword_sources),
            'total_sources_found': sum(info['sources_count'] for info in keyword_sources.values()),
            'total_urls_extracted': sum(info['extracted_count'] for info in keyword_sources.values()),
            'keyword_sources': keyword_sources,
            'all_sources': all_sources,
            'domain_statistics': dict(sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:20]),
            'extraction_success_rate': len(all_sources) / max(sum(info['sources_count'] for info in keyword_sources.values()), 1) * 100
        }
        
        return report
    
    def print_sources_summary(self, sources_report: Dict[str, Any]):
        """打印网页源汇总"""
        print(f"\n{'='*80}")
        print("网页源汇总报告")
        print(f"{'='*80}")
        print(f"汇总时间: {sources_report['summary_time']}")
        print(f"分析关键词数: {sources_report['total_keywords']}")
        print(f"总搜索网页数: {sources_report['total_sources_found']}")
        print(f"总提取URL数: {sources_report['total_urls_extracted']}")
        print(f"提取成功率: {sources_report['extraction_success_rate']:.1f}%")
        
        print(f"\n{'='*80}")
        print("各关键词源统计:")
        print(f"{'='*80}")
        for keyword, info in sources_report['keyword_sources'].items():
            print(f"{keyword}: 搜索到 {info['sources_count']} 个，提取 {info['extracted_count']} 个URL")
        
        print(f"\n{'='*80}")
        print("主要域名分布:")
        print(f"{'='*80}")
        for domain, count in list(sources_report['domain_statistics'].items())[:10]:
            print(f"{domain}: {count} 个URL")


async def main():
    """主函数 - 演示增强版集成分析功能"""
    print("增强版集成分析工具演示")
    print("="*80)
    
    # 创建增强版集成分析器
    analyzer = EnhancedIntegratedAnalyzer()
    
    # 单个关键词增强分析
    print("1. 单个关键词增强分析演示")
    result = await analyzer.search_analyze_and_extract_sources("小鸡科技")
    
    if result:
        print("✅ 单个关键词增强分析完成")
        
        # 显示源URL信息
        sources_urls = result['search_results'].get('sources_urls', [])
        if sources_urls:
            print(f"\n获取到 {len(sources_urls)} 个网页源URL:")
            for i, source in enumerate(sources_urls[:3], 1):
                if isinstance(source, dict):
                    print(f"{i}. {source.get('title', 'N/A')[:50]}...")
                    print(f"   {source.get('url', 'N/A')}")
    else:
        print("❌ 单个关键词增强分析失败")
    
    # 批量关键词增强分析（示例，注释掉以避免过长时间）
    # keywords = ["小鸡科技", "游戏外设"]
    # queries = {
    #     "小鸡科技": "小鸡科技的最新信息，包括公司背景、业务范围、最新动态",
    #     "游戏外设": "游戏外设行业的发展趋势和主要厂商"
    # }
    # 
    # print("\n2. 批量关键词增强分析演示")
    # batch_results = await analyzer.batch_enhanced_analyze(keywords, queries)
    # 
    # if batch_results:
    #     # 生成网页源汇总报告
    #     sources_report = analyzer.generate_sources_summary_report(batch_results)
    #     analyzer.print_sources_summary(sources_report)


if __name__ == "__main__":
    asyncio.run(main()) 