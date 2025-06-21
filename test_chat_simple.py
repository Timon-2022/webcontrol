#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的聊天搜索测试
"""

import asyncio
import json
from web_scraper_fixed import WebScraper

async def test_search():
    """测试搜索功能"""
    scraper = WebScraper()
    
    # 测试关键词
    query = "人工智能"
    
    print(f"🔍 开始测试搜索功能，关键词: {query}")
    
    try:
        # 测试前3个网站
        from config import AI_WEBSITES
        test_websites = AI_WEBSITES[:3]  # 只测试前3个网站
        
        if not await scraper.init_browser():
            print("❌ 浏览器初始化失败")
            return
        
        all_results = []
        
        for website in test_websites:
            print(f"🌐 正在测试 {website['name']}...")
            try:
                results = await scraper.search_website(website, query)
                all_results.extend(results)
                print(f"✅ {website['name']} 完成，获取 {len(results)} 个结果")
            except Exception as e:
                print(f"❌ {website['name']} 失败: {e}")
        
        await scraper.close_browser()
        
        # 保存结果
        if all_results:
            filename = scraper.save_results(all_results, query)
            print(f"\n📊 测试完成！")
            print(f"📁 总共获取 {len(all_results)} 个结果")
            print(f"💾 结果已保存到: {filename}")
            
            # 显示前几个结果
            print(f"\n📝 前3个结果预览:")
            for i, result in enumerate(all_results[:3]):
                print(f"  {i+1}. {result['website']}: {result['title'][:50]}...")
        else:
            print("❌ 未获取到任何结果")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        await scraper.close_browser()

if __name__ == "__main__":
    asyncio.run(test_search()) 