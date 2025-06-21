#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
尝试提取DeepSeek回复中的网页来源信息
分析数字引用和可能的来源链接
"""

import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def extract_web_sources():
    """尝试提取网页来源"""
    print("=" * 70)
    print("🔍 DeepSeek 网页来源提取 - 分析引用信息")
    print("=" * 70)
    
    # 从之前的结果文件中分析
    latest_file = "data/deepseek_complete_content_20250621_122531.json"
    
    if os.path.exists(latest_file):
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        content = data['paragraphs_with_keyword'][0]['content']
        print(f"📖 分析内容长度: {len(content)} 字符")
        
        # 查找数字引用模式
        print("\n🔍 查找数字引用...")
        number_patterns = [
            r'(\d+)[。.]',  # 数字后跟句号
            r'(\d+)、',     # 数字后跟顿号
            r'\[(\d+)\]',   # 方括号数字
            r'（(\d+)）',   # 圆括号数字
            r'(\d+)$',      # 行末数字
        ]
        
        found_numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_numbers.extend(matches)
                print(f"  模式 '{pattern}' 找到: {matches}")
        
        # 去重并排序
        unique_numbers = sorted(list(set(found_numbers)), key=lambda x: int(x))
        print(f"📊 发现的引用数字: {unique_numbers}")
        
        # 分析内容结构
        print("\n📝 分析内容结构...")
        
        # 查找公司信息段落
        sections = {
            '公司背景': re.search(r'1\.\s*公司背景([^2]*)', content),
            '主要业务': re.search(r'2\.\s*主要业务([^3]*)', content),
            '发展历程': re.search(r'3\.\s*发展历程([^4]*)', content),
        }
        
        structured_info = {}
        for section_name, match in sections.items():
            if match:
                section_content = match.group(1).strip()
                structured_info[section_name] = section_content
                print(f"  ✅ {section_name}: {len(section_content)} 字符")
                
                # 在每个段落中查找数字引用
                section_numbers = re.findall(r'(\d+)', section_content)
                if section_numbers:
                    print(f"    引用数字: {section_numbers}")
        
        # 查找具体的产品和合作信息
        print("\n🔍 提取具体信息...")
        
        # 产品信息
        products = re.findall(r'([A-Z][A-Za-z0-9\s]+手柄|[A-Za-z0-9]+系列)', content)
        print(f"📱 发现产品: {products}")
        
        # 合作伙伴
        partners = re.findall(r'(微软|迪士尼|漫威|米哈游|Xbox|Switch)', content)
        print(f"🤝 合作伙伴: {list(set(partners))}")
        
        # 数据指标
        metrics = re.findall(r'(\d+(?:万|千万|亿)?(?:用户|款游戏|年))', content)
        print(f"📊 数据指标: {metrics}")
        
        # 地点信息
        locations = re.findall(r'(广州|深圳|香港|美国|洛杉矶)', content)
        print(f"🌍 涉及地点: {list(set(locations))}")
        
        # 保存分析结果
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'source_file': latest_file,
            'analysis_type': 'web_sources_extraction',
            'found_numbers': unique_numbers,
            'structured_sections': structured_info,
            'extracted_entities': {
                'products': products,
                'partners': list(set(partners)),
                'metrics': metrics,
                'locations': list(set(locations))
            },
            'total_references': len(unique_numbers),
            'content_length': len(content)
        }
        
        # 保存分析结果
        output_file = f"data/deepseek_sources_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 来源分析已保存到: {output_file}")
        print(f"📊 分析结果:")
        print(f"  - 发现引用数字: {len(unique_numbers)} 个")
        print(f"  - 结构化段落: {len(structured_info)} 个")
        print(f"  - 产品信息: {len(products)} 个")
        print(f"  - 合作伙伴: {len(set(partners))} 个")
        print(f"  - 数据指标: {len(metrics)} 个")
        
        # 推测可能的网页来源
        print(f"\n💡 推测的50个网页可能包括:")
        print(f"  - 官方网站和产品页面")
        print(f"  - 新闻报道和媒体文章")
        print(f"  - 企业信息查询网站")
        print(f"  - 游戏行业资讯网站")
        print(f"  - 合作伙伴官方公告")
        print(f"  - 电商平台产品页面")
        print(f"  - 投资和企业数据库")
        print(f"  - 社交媒体和论坛讨论")
        
    else:
        print(f"❌ 未找到数据文件: {latest_file}")

if __name__ == "__main__":
    asyncio.run(extract_web_sources())
