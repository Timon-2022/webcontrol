#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试DeepSeek网页源提取功能
"""

import asyncio
import os
from deepseek_web_sources_extractor import DeepSeekWebSourcesExtractor


async def test_sources_extraction():
    """测试网页源提取功能"""
    print("="*60)
    print("测试DeepSeek网页源提取功能")
    print("="*60)
    
    # 检查登录状态
    if not os.path.exists("login_state.json"):
        print("⚠️  警告: 未找到登录状态文件 login_state.json")
        print("   请先运行 login_manager.py 进行手动登录")
        return
    
    extractor = DeepSeekWebSourcesExtractor()
    
    try:
        # 初始化浏览器
        print("正在初始化浏览器...")
        if not await extractor.init_browser():
            print("❌ 浏览器初始化失败")
            return
        
        # 测试查询
        query = "小鸡科技的最新信息，包括公司背景、业务范围、最新动态"
        print(f"正在执行搜索: {query}")
        print("注意: 这个过程可能需要30-60秒...")
        
        # 执行搜索并提取源
        result = await extractor.search_and_extract_sources(query)
        
        # 显示结果摘要
        extractor.print_sources_summary(result)
        
        # 保存详细结果
        if result['success']:
            filename = extractor.save_sources_result(result)
            print(f"\n✅ 详细结果已保存到: {filename}")
            
            # 如果获取到了URL，显示更多信息
            if result['sources_urls']:
                print(f"\n获取到的网页源URL:")
                print("-" * 60)
                for i, source in enumerate(result['sources_urls'], 1):
                    if isinstance(source, dict):
                        print(f"{i}. 标题: {source.get('title', 'N/A')}")
                        print(f"   URL: {source.get('url', 'N/A')}")
                        print(f"   提取方式: {source.get('selector', 'N/A')}")
                        print()
                    else:
                        print(f"{i}. {source}")
                        print()
            else:
                print("\n⚠️  未能获取到具体的网页URL")
                print("   可能的原因:")
                print("   - 页面结构发生变化")
                print("   - 需要更多时间加载")
                print("   - 源链接不可点击")
        else:
            print(f"\n❌ 搜索失败: {result.get('error', '未知错误')}")
    
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
    
    finally:
        # 关闭浏览器
        print("\n正在关闭浏览器...")
        await extractor.close_browser()
        print("✅ 测试完成")


async def main():
    """主函数"""
    print("DeepSeek网页源提取测试")
    print("="*60)
    print("此工具将:")
    print("1. 向DeepSeek发送搜索查询")
    print("2. 等待AI回复完成")
    print("3. 查找并点击'已搜索到XX个网页'链接")
    print("4. 提取具体的网页URL列表")
    print("5. 保存所有结果到JSON文件")
    print()
    
    # 确认执行
    confirm = input("是否继续执行测试？(y/n): ").strip().lower()
    if confirm == 'y':
        await test_sources_extraction()
    else:
        print("测试已取消")


if __name__ == "__main__":
    asyncio.run(main()) 