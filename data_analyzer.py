#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析模块 - 分析AI搜索结果
"""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Any

import jieba
import pandas as pd
import numpy as np
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'PingFang SC']
plt.rcParams['axes.unicode_minus'] = False

class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self, results_dir: str = "results"):
        """
        初始化数据分析器
        
        Args:
            results_dir: 结果文件目录
        """
        self.results_dir = results_dir
        self.stop_words = self._load_stop_words()
        
    def _load_stop_words(self) -> set:
        """加载停用词"""
        stop_words = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '它', '他', '她', '我们', '你们', '他们', '她们', '它们',
            '这个', '那个', '这些', '那些', '什么', '怎么', '为什么', '哪里', '哪个', '如何', '可以', '能够', '应该', '需要', '想要', '希望', '觉得', '认为', '知道', '了解', '明白', '清楚', '发现', '找到', '得到', '获得', '拥有', '具有', '包含', '包括', '涉及', '关于', '对于', '根据', '按照', '通过', '利用', '使用', '采用', '运用', '进行', '实现', '完成', '达到', '实现', '成为', '变成', '作为', '当作', '被', '给', '让', '使', '令', '叫', '请', '要求', '建议', '推荐', '提供', '提出', '提到', '说明', '表示', '表明', '显示', '展示', '证明', '证实', '确认', '确定', '肯定', '否定', '同意', '反对', '支持', '赞成', '反对', '拒绝', '接受', '承认', '否认', '相信', '怀疑', '担心', '害怕', '喜欢', '讨厌', '爱', '恨', '开心', '高兴', '快乐', '兴奋', '激动', '满意', '不满', '失望', '难过', '伤心', '痛苦', '困难', '容易', '简单', '复杂', '重要', '关键', '主要', '次要', '基本', '主要', '核心', '中心', '焦点', '重点', '关键点', '要点', '特点', '特色', '特征', '优点', '缺点', '问题', '困难', '挑战', '机会', '可能', '或许', '也许', '大概', '可能', '肯定', '一定', '必须', '应该', '需要', '想要', '希望', '打算', '计划', '准备', '开始', '结束', '完成', '继续', '停止', '暂停', '休息', '工作', '学习', '生活', '娱乐', '休闲', '运动', '锻炼', '健康', '安全', '危险', '风险', '机会', '挑战', '成功', '失败', '胜利', '失败', '赢', '输', '好', '坏', '对', '错', '正确', '错误', '真', '假', '新', '老', '旧', '大', '小', '多', '少', '高', '低', '长', '短', '宽', '窄', '厚', '薄', '重', '轻', '快', '慢', '早', '晚', '前', '后', '左', '右', '上', '下', '内', '外', '里', '外面', '这里', '那里', '到处', '处处', '总是', '经常', '有时', '偶尔', '从来', '从不', '永远', '一直', '始终', '最终', '最后', '首先', '然后', '接着', '最后', '总之', '因此', '所以', '但是', '不过', '然而', '虽然', '尽管', '即使', '如果', '假如', '除非', '只要', '只有', '不仅', '而且', '还', '也', '又', '再', '还是', '或者', '还是', '要么', '不是', '就是', '既然', '由于', '因为', '为了', '以便', '以免', '免得', '省得', '除了', '除非', '只要', '只有', '不管', '无论', '不论', '无论如何', '总之', '总而言之', '一般来说', '通常', '一般', '普通', '平常', '正常', '异常', '特殊', '特别', '尤其', '特别是', '比如', '例如', '譬如', '诸如', '等等', '之类', '以及', '和', '与', '同', '跟', '及', '以及', '还有', '另外', '此外', '而且', '并且', '同时', '一边', '一面', '一方面', '另一方面', '相反', '相对', '比较', '对比', '相比', '与此同时', '同时', '此时', '这时', '那时', '当时', '现在', '目前', '如今', '今天', '昨天', '明天', '后天', '前天', '今年', '去年', '明年', '前年', '后年', '这年', '那年', '今天', '昨天', '明天', '今晚', '昨晚', '明晚', '上午', '下午', '晚上', '夜里', '半夜', '凌晨', '早上', '中午', '傍晚', '黄昏', '深夜', '白天', '夜晚'
        ])
        return stop_words
    
    def analyze_keyword_frequency(self, texts: List[str], keyword: str) -> Dict[str, Any]:
        """
        分析关键词频度
        
        Args:
            texts: 文本列表
            keyword: 目标关键词
            
        Returns:
            分析结果字典
        """
        # 合并所有文本
        combined_text = ' '.join(texts)
        
        # 使用jieba进行中文分词
        words = list(jieba.cut(combined_text))
        
        # 过滤停用词和标点符号
        filtered_words = [
            word.strip() for word in words 
            if word.strip() and word.strip() not in self.stop_words
            and len(word.strip()) > 1 and not re.match(r'^[^\w\s]+$', word.strip())
        ]
        
        # 统计词频
        word_counts = Counter(filtered_words)
        
        # 计算关键词频度
        keyword_count = word_counts.get(keyword, 0)
        total_words = len(filtered_words)
        keyword_frequency = keyword_count / total_words if total_words > 0 else 0
        
        # 找出相关词汇（包含关键词的词汇）
        related_words = {
            word: count for word, count in word_counts.items()
            if keyword in word or word in keyword
        }
        
        return {
            'keyword': keyword,
            'keyword_count': keyword_count,
            'total_words': total_words,
            'keyword_frequency': keyword_frequency,
            'keyword_percentage': keyword_frequency * 100,
            'related_words': related_words,
            'top_words': dict(word_counts.most_common(20)),
            'total_texts': len(texts)
        }
    
    def analyze_sentiment(self, texts: List[str]) -> Dict[str, Any]:
        """
        分析情绪倾向
        
        Args:
            texts: 文本列表
            
        Returns:
            情绪分析结果
        """
        sentiments = []
        
        for text in texts:
            # 使用TextBlob进行情绪分析
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 到 1，负数表示负面，正数表示正面
            subjectivity = blob.sentiment.subjectivity  # 0 到 1，0表示客观，1表示主观
            
            sentiments.append({
                'polarity': polarity,
                'subjectivity': subjectivity,
                'sentiment_label': self._get_sentiment_label(polarity)
            })
        
        # 计算平均情绪
        avg_polarity = np.mean([s['polarity'] for s in sentiments])
        avg_subjectivity = np.mean([s['subjectivity'] for s in sentiments])
        
        # 统计情绪分布
        sentiment_distribution = Counter([s['sentiment_label'] for s in sentiments])
        
        return {
            'individual_sentiments': sentiments,
            'average_polarity': avg_polarity,
            'average_subjectivity': avg_subjectivity,
            'overall_sentiment': self._get_sentiment_label(avg_polarity),
            'sentiment_distribution': dict(sentiment_distribution),
            'total_texts': len(texts)
        }
    
    def _get_sentiment_label(self, polarity: float) -> str:
        """根据极性值返回情绪标签"""
        if polarity > 0.1:
            return '积极'
        elif polarity < -0.1:
            return '消极'
        else:
            return '中性'
    
    def analyze_authority(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析权威性
        
        Args:
            results: 搜索结果列表
            
        Returns:
            权威性分析结果
        """
        authority_scores = []
        
        for result in results:
            website = result.get('website', '')
            content_length = len(result.get('content', ''))
            has_references = 'references' in result and len(result['references']) > 0
            
            # 基于网站类型计算权威性得分
            base_score = self._get_website_authority_score(website)
            
            # 基于内容长度调整得分
            length_bonus = min(content_length / 1000, 2.0)  # 最多加2分
            
            # 基于是否有引用调整得分
            reference_bonus = 1.0 if has_references else 0
            
            authority_score = base_score + length_bonus + reference_bonus
            authority_scores.append({
                'website': website,
                'base_score': base_score,
                'length_bonus': length_bonus,
                'reference_bonus': reference_bonus,
                'total_score': authority_score
            })
        
        # 计算平均权威性
        avg_authority = np.mean([s['total_score'] for s in authority_scores])
        
        return {
            'individual_scores': authority_scores,
            'average_authority': avg_authority,
            'authority_level': self._get_authority_level(avg_authority),
            'total_sources': len(results)
        }
    
    def _get_website_authority_score(self, website: str) -> float:
        """根据网站类型返回基础权威性得分"""
        website_lower = website.lower()
        
        # 高权威性网站
        if any(domain in website_lower for domain in [
            'edu', 'gov', 'org', 'wikipedia', 'baidu', 'google', 'microsoft', 'openai'
        ]):
            return 8.0
        
        # 中等权威性网站
        elif any(domain in website_lower for domain in [
            'news', 'tech', 'science', 'research', 'academic'
        ]):
            return 6.0
        
        # 一般权威性网站
        else:
            return 4.0
    
    def _get_authority_level(self, score: float) -> str:
        """根据权威性得分返回权威性等级"""
        if score >= 8.0:
            return '高权威性'
        elif score >= 6.0:
            return '中等权威性'
        else:
            return '一般权威性'
    
    def analyze_relevance(self, texts: List[str], keyword: str) -> Dict[str, Any]:
        """
        分析相关性
        
        Args:
            texts: 文本列表
            keyword: 目标关键词
            
        Returns:
            相关性分析结果
        """
        relevance_scores = []
        
        for i, text in enumerate(texts):
            # 计算关键词在文本中的出现次数
            keyword_count = text.lower().count(keyword.lower())
            
            # 计算文本长度
            text_length = len(text)
            
            # 计算关键词密度
            keyword_density = keyword_count / text_length if text_length > 0 else 0
            
            # 计算相关词汇出现次数
            related_words = self._get_related_words(keyword)
            related_count = sum(text.lower().count(word.lower()) for word in related_words)
            
            # 计算相关性得分
            relevance_score = (keyword_count * 2 + related_count) / max(text_length / 100, 1)
            
            relevance_scores.append({
                'text_index': i,
                'keyword_count': keyword_count,
                'related_count': related_count,
                'text_length': text_length,
                'keyword_density': keyword_density,
                'relevance_score': relevance_score
            })
        
        # 计算平均相关性
        avg_relevance = np.mean([s['relevance_score'] for s in relevance_scores])
        
        return {
            'individual_relevance': relevance_scores,
            'average_relevance': avg_relevance,
            'relevance_level': self._get_relevance_level(avg_relevance),
            'total_texts': len(texts)
        }
    
    def _get_related_words(self, keyword: str) -> List[str]:
        """获取与关键词相关的词汇"""
        # 这里可以根据具体关键词定制相关词汇
        if '科技' in keyword:
            return ['技术', '创新', '研发', '产品', '服务', '公司', '企业', '业务', '发展', '市场']
        else:
            return ['相关', '关联', '相似', '类似', '同类', '相应', '对应']
    
    def _get_relevance_level(self, score: float) -> str:
        """根据相关性得分返回相关性等级"""
        if score >= 0.5:
            return '高相关性'
        elif score >= 0.2:
            return '中等相关性'
        else:
            return '低相关性'
    
    def generate_word_cloud(self, texts: List[str], keyword: str, output_path: str = None) -> str:
        """
        生成词云图
        
        Args:
            texts: 文本列表
            keyword: 关键词
            output_path: 输出路径
            
        Returns:
            词云图文件路径
        """
        # 合并所有文本
        combined_text = ' '.join(texts)
        
        # 使用jieba进行中文分词
        words = list(jieba.cut(combined_text))
        
        # 过滤停用词
        filtered_words = [
            word for word in words 
            if word.strip() and word.strip() not in self.stop_words
            and len(word.strip()) > 1
        ]
        
        # 合并词汇
        text_for_cloud = ' '.join(filtered_words)
        
        if not output_path:
            output_path = f"wordcloud_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # 生成词云
        wordcloud = WordCloud(
            width=800,
            height=600,
            background_color='white',
            max_words=100,
            font_path=None,  # 如果有中文字体文件，可以指定路径
            colormap='viridis'
        ).generate(text_for_cloud)
        
        # 保存词云图
        plt.figure(figsize=(10, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'关键词 "{keyword}" 相关词云图', fontsize=16, pad=20)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_comprehensive_report(self, results: List[Dict[str, Any]], keyword: str) -> Dict[str, Any]:
        """
        生成综合分析报告
        
        Args:
            results: 搜索结果列表
            keyword: 关键词
            
        Returns:
            综合分析报告
        """
        # 提取所有文本内容
        texts = [result.get('content', '') for result in results if result.get('content')]
        
        # 进行各项分析
        frequency_analysis = self.analyze_keyword_frequency(texts, keyword)
        sentiment_analysis = self.analyze_sentiment(texts)
        authority_analysis = self.analyze_authority(results)
        relevance_analysis = self.analyze_relevance(texts, keyword)
        
        # 生成词云图
        wordcloud_path = self.generate_word_cloud(texts, keyword)
        
        # 生成综合报告
        report = {
            'analysis_time': datetime.now().isoformat(),
            'keyword': keyword,
            'total_sources': len(results),
            'total_texts': len(texts),
            'frequency_analysis': frequency_analysis,
            'sentiment_analysis': sentiment_analysis,
            'authority_analysis': authority_analysis,
            'relevance_analysis': relevance_analysis,
            'wordcloud_path': wordcloud_path,
            'summary': {
                'keyword_frequency': f"{frequency_analysis['keyword_percentage']:.2f}%",
                'overall_sentiment': sentiment_analysis['overall_sentiment'],
                'authority_level': authority_analysis['authority_level'],
                'relevance_level': relevance_analysis['relevance_level']
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str = None) -> str:
        """
        保存分析报告
        
        Args:
            report: 分析报告
            output_path: 输出路径
            
        Returns:
            报告文件路径
        """
        if not output_path:
            keyword = report.get('keyword', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"analysis_report_{keyword}_{timestamp}.json"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def print_summary(self, report: Dict[str, Any]):
        """打印分析摘要"""
        print(f"\n{'='*60}")
        print(f"关键词分析报告: {report['keyword']}")
        print(f"{'='*60}")
        print(f"分析时间: {report['analysis_time']}")
        print(f"数据源数量: {report['total_sources']}")
        print(f"文本数量: {report['total_texts']}")
        print(f"\n{'='*60}")
        print("分析结果摘要:")
        print(f"{'='*60}")
        print(f"关键词频度: {report['summary']['keyword_frequency']}")
        print(f"整体情绪: {report['summary']['overall_sentiment']}")
        print(f"权威性等级: {report['summary']['authority_level']}")
        print(f"相关性等级: {report['summary']['relevance_level']}")
        print(f"\n词云图已保存: {report['wordcloud_path']}")
        print(f"{'='*60}")


def main():
    """主函数 - 演示数据分析功能"""
    analyzer = DataAnalyzer()
    
    # 示例数据
    sample_results = [
        {
            'website': 'DeepSeek',
            'content': '小鸡科技是一家专注于游戏外设的科技公司，成立于2010年，总部位于广州。公司主要业务包括游戏手柄、键盘、鼠标等外设产品的研发和销售。',
            'references': ['ref1', 'ref2']
        },
        {
            'website': 'Kimi',
            'content': '广州小鸡快跑网络科技有限公司，简称小鸡科技，是一家创新型科技企业。公司致力于为用户提供优质的游戏体验，产品涵盖多个平台。',
            'references': []
        }
    ]
    
    # 生成综合分析报告
    report = analyzer.generate_comprehensive_report(sample_results, '小鸡科技')
    
    # 打印摘要
    analyzer.print_summary(report)
    
    # 保存报告
    report_path = analyzer.save_report(report)
    print(f"\n完整报告已保存: {report_path}")


if __name__ == "__main__":
    main() 