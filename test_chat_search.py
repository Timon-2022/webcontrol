#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from web_scraper import WebScraper
from config import AI_WEBSITES

async def test_chat_search():
    """测试聊天搜索功能"""
    print("=== 聊天搜索功能测试 ===")
    
    scraper = WebScraper()
    query = "小鸟科技"
    
    try:
        # 初始化浏览器
        print("正在初始化浏览器...")
        if not await scraper.init_browser():
            print("浏览器初始化失败")
            return
        
        print("✓ 浏览器初始化成功")
        
        # 只测试聊天形式的网站
        chat_websites = [site for site in AI_WEBSITES if site.get('is_chat', False)]
        
        print(f"找到 {len(chat_websites)} 个聊天网站:")
        for site in chat_websites:
            print(f"  - {site['name']}: {site['url']}")
        
        all_results = []
        
        for website in chat_websites:
            print(f"\n正在测试 {website['name']}...")
            try:
                results = await scraper.search_website(website, query)
                if results:
                    print(f"✓ 从 {website['name']} 获取到 {len(results)} 个结果")
                    all_results.extend(results)
                    
                    # 显示第一个结果
                    if results:
                        first_result = results[0]
                        print(f"  回复内容: {first_result['content'][:100]}...")
                else:
                    print(f"✗ 从 {website['name']} 未获取到结果")
                
                # 等待一下再测试下一个
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"✗ 测试 {website['name']} 时出错: {e}")
                continue
        
        # 保存结果
        if all_results:
            filename = scraper.save_results(all_results, query)
            print(f"\n✓ 测试完成！共获取到 {len(all_results)} 个聊天回复")
            print(f"结果已保存到: {filename}")
            
            # 显示所有结果摘要
            print("\n=== 聊天回复摘要 ===")
            for i, result in enumerate(all_results, 1):
                print(f"{i}. {result['website']}: {result['content'][:80]}...")
        else:
            print("\n✗ 未获取到任何聊天回复")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        await scraper.close_browser()

if __name__ == "__main__":
    asyncio.run(test_chat_search()) 