import json
import os
import re
from typing import Dict, List, Tuple
import logging
from datetime import datetime

import pandas as pd
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 下载NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from config import DATA_CONFIG

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
    def load_search_results(self, file_path: str) -> Dict:
        """加载搜索结果文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载搜索结果文件: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载搜索结果文件失败: {e}")
            return None
    
    def calculate_keyword_frequency(self, results: List[Dict], query: str) -> Dict:
        """计算关键词频度"""
        frequency_data = {
            'total_occurrences': 0,
            'website_frequency': {},
            'content_frequency': {},
            'title_frequency': {}
        }
        
        # 将查询词转换为小写并分词
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        for result in results:
            website = result['website']
            title = result['title'].lower()
            content = result['content'].lower()
            
            # 统计标题中的关键词出现次数
            title_count = sum(1 for word in query_words if word in title)
            if title_count > 0:
                frequency_data['title_frequency'][website] = frequency_data['title_frequency'].get(website, 0) + title_count
            
            # 统计内容中的关键词出现次数
            content_count = sum(1 for word in query_words if word in content)
            if content_count > 0:
                frequency_data['content_frequency'][website] = frequency_data['content_frequency'].get(website, 0) + content_count
            
            # 统计总出现次数
            total_count = title_count + content_count
            if total_count > 0:
                frequency_data['website_frequency'][website] = frequency_data['website_frequency'].get(website, 0) + total_count
                frequency_data['total_occurrences'] += total_count
        
        return frequency_data
    
    def calculate_relevance_score(self, result: Dict, query: str) -> float:
        """计算相关性分数"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        title = result['title'].lower()
        content = result['content'].lower()
        
        # 标题权重更高
        title_matches = sum(1 for word in query_words if word in title)
        content_matches = sum(1 for word in query_words if word in content)
        
        # 计算相关性分数 (0-1)
        title_score = min(title_matches / len(query_words), 1.0) * 0.6
        content_score = min(content_matches / len(query_words), 1.0) * 0.4
        
        return title_score + content_score
    
    def analyze_sentiment(self, text: str) -> Dict:
        """分析文本情绪"""
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment
            
            # 将情绪分数转换为标签
            if sentiment.polarity > 0.1:
                sentiment_label = "积极"
            elif sentiment.polarity < -0.1:
                sentiment_label = "消极"
            else:
                sentiment_label = "中性"
            
            return {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity,
                'label': sentiment_label
            }
        except Exception as e:
            logger.error(f"情绪分析失败: {e}")
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'label': "未知"
            }
    
    def calculate_authority_score(self, result: Dict) -> float:
        """计算权威性分数"""
        authority_score = 0.0
        
        # 基于网站知名度的权威性评分
        authority_websites = {
            'OpenAI': 0.9,
            'Anthropic': 0.85,
            'Google AI': 0.9,
            'Microsoft AI': 0.85,
            'Meta AI': 0.8,
            'DeepMind': 0.9,
            'Hugging Face': 0.8,
            'Stability AI': 0.75,
            'Cohere': 0.7,
            'Claude': 0.85,
            'Perplexity': 0.7,
            'You.com': 0.65,
            'Bard': 0.8,
            'ChatGPT': 0.9,
            'Bing Chat': 0.8,
            'Midjourney': 0.75,
            'DALL-E': 0.85,
            'Runway': 0.7,
            'ElevenLabs': 0.65,
            'Replicate': 0.7
        }
        
        website = result['website']
        if website in authority_websites:
            authority_score += authority_websites[website] * 0.6
        
        # 基于内容长度的权威性评分
        content_length = len(result['content'])
        if content_length > 200:
            authority_score += 0.2
        elif content_length > 100:
            authority_score += 0.1
        
        # 基于是否有链接的权威性评分
        if result['link']:
            authority_score += 0.1
        
        # 基于是否有图片的权威性评分
        if result['image']:
            authority_score += 0.1
        
        return min(authority_score, 1.0)
    
    def analyze_results(self, results: List[Dict], query: str) -> Dict:
        """分析所有搜索结果"""
        analysis_results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'total_results': len(results),
            'websites_analyzed': len(set(r['website'] for r in results)),
            'frequency_analysis': self.calculate_keyword_frequency(results, query),
            'detailed_analysis': []
        }
        
        for result in results:
            # 计算相关性
            relevance_score = self.calculate_relevance_score(result, query)
            
            # 分析情绪
            sentiment = self.analyze_sentiment(result['content'])
            
            # 计算权威性
            authority_score = self.calculate_authority_score(result)
            
            # 综合评分
            overall_score = (relevance_score * 0.4 + 
                           (sentiment['polarity'] + 1) * 0.2 + 
                           authority_score * 0.4)
            
            detailed_analysis = {
                'website': result['website'],
                'title': result['title'],
                'link': result['link'],
                'relevance_score': relevance_score,
                'sentiment': sentiment,
                'authority_score': authority_score,
                'overall_score': overall_score,
                'rank': result['rank']
            }
            
            analysis_results['detailed_analysis'].append(detailed_analysis)
        
        # 按综合评分排序
        analysis_results['detailed_analysis'].sort(
            key=lambda x: x['overall_score'], 
            reverse=True
        )
        
        return analysis_results
    
    def generate_summary_report(self, analysis_results: Dict) -> str:
        """生成摘要报告"""
        summary = f"""
=== AI网站搜索结果分析报告 ===

查询关键词: {analysis_results['query']}
分析时间: {analysis_results['timestamp']}
总结果数: {analysis_results['total_results']}
分析网站数: {analysis_results['websites_analyzed']}

=== 关键词频度分析 ===
总出现次数: {analysis_results['frequency_analysis']['total_occurrences']}

网站频度排名:
"""
        
        # 网站频度排名
        website_freq = analysis_results['frequency_analysis']['website_frequency']
        sorted_websites = sorted(website_freq.items(), key=lambda x: x[1], reverse=True)
        
        for website, count in sorted_websites[:10]:
            summary += f"  {website}: {count}次\n"
        
        summary += "\n=== 相关性分析 ===\n"
        # 相关性最高的结果
        top_relevant = analysis_results['detailed_analysis'][:5]
        for i, result in enumerate(top_relevant, 1):
            summary += f"  {i}. {result['website']} - {result['title'][:50]}... (相关性: {result['relevance_score']:.2f})\n"
        
        summary += "\n=== 情绪分析 ===\n"
        # 情绪分布
        sentiment_counts = {}
        for result in analysis_results['detailed_analysis']:
            label = result['sentiment']['label']
            sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
        
        for label, count in sentiment_counts.items():
            percentage = (count / len(analysis_results['detailed_analysis'])) * 100
            summary += f"  {label}: {count}个结果 ({percentage:.1f}%)\n"
        
        summary += "\n=== 权威性分析 ===\n"
        # 权威性最高的网站
        authority_scores = {}
        for result in analysis_results['detailed_analysis']:
            website = result['website']
            if website not in authority_scores:
                authority_scores[website] = []
            authority_scores[website].append(result['authority_score'])
        
        avg_authority = {website: sum(scores)/len(scores) for website, scores in authority_scores.items()}
        sorted_authority = sorted(avg_authority.items(), key=lambda x: x[1], reverse=True)
        
        for website, score in sorted_authority[:5]:
            summary += f"  {website}: {score:.2f}\n"
        
        summary += "\n=== 综合推荐 ===\n"
        # 综合评分最高的结果
        top_overall = analysis_results['detailed_analysis'][:3]
        for i, result in enumerate(top_overall, 1):
            summary += f"  {i}. {result['website']} - {result['title'][:50]}... (综合评分: {result['overall_score']:.2f})\n"
        
        return summary
    
    def save_analysis(self, analysis_results: Dict, query: str):
        """保存分析结果"""
        os.makedirs(DATA_CONFIG['output_dir'], exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_CONFIG['output_dir']}/analysis_results_{query}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        # 保存摘要报告
        summary_filename = f"{DATA_CONFIG['output_dir']}/summary_report_{query}_{timestamp}.txt"
        summary = self.generate_summary_report(analysis_results)
        
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"分析结果已保存到: {filename}")
        logger.info(f"摘要报告已保存到: {summary_filename}")
        
        return filename, summary_filename

def main():
    """主函数"""
    analyzer = AIAnalyzer()
    
    # 获取搜索结果文件
    data_dir = DATA_CONFIG['output_dir']
    if not os.path.exists(data_dir):
        print("数据目录不存在，请先运行 web_scraper.py 获取搜索结果")
        return
    
    # 查找最新的搜索结果文件
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and 'search_results' in f]
    if not json_files:
        print("未找到搜索结果文件，请先运行 web_scraper.py 获取搜索结果")
        return
    
    latest_file = max(json_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
    file_path = os.path.join(data_dir, latest_file)
    
    print(f"正在分析文件: {file_path}")
    
    # 加载搜索结果
    search_data = analyzer.load_search_results(file_path)
    if not search_data:
        return
    
    # 分析结果
    print("正在分析搜索结果...")
    analysis_results = analyzer.analyze_results(search_data['results'], search_data['query'])
    
    # 保存分析结果
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

if __name__ == "__main__":
    main() 