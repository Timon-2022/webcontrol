#!/usr/bin/env python3
"""
精准参考来源提取器
专门查找具有特定CSS类名的真正参考来源标题，提高点击成功率
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urlparse

async def extract_page_summary(page):
    """提取页面的简要信息，生成100字左右的简报"""
    try:
        url = page.url
        title = await page.title()
        
        # 获取描述
        description = ""
        try:
            desc_element = await page.query_selector('meta[name="description"]')
            if desc_element:
                description = await desc_element.get_attribute('content') or ""
        except:
            pass
        
        # 获取主要内容
        content = ""
        content_selectors = ['article', 'main', '.content', '.article']
        
        for selector in content_selectors:
            try:
                content_element = await page.query_selector(selector)
                if content_element:
                    content_text = await content_element.inner_text()
                    if len(content_text) > len(content):
                        content = content_text
            except:
                continue
        
        # 生成简报
        summary = ""
        if description:
            summary = description[:100] + "..." if len(description) > 100 else description
        elif content:
            content_clean = content.replace('\n', ' ').replace('\t', ' ').strip()
            summary = content_clean[:100] + "..." if len(content_clean) > 100 else content_clean
        
        # 获取域名
        domain = ""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
        except:
            pass
        
        return {
            "url": url,
            "title": title,
            "domain": domain,
            "summary": summary
        }
    except Exception as e:
        print(f"提取页面信息出错: {e}")
        return {"url": page.url, "title": "", "domain": "", "summary": ""}

async def main():
    """主函数"""
    print("🎯 精准参考来源提取器")
    print("专门查找具有特定CSS类名的真正参考来源标题")
    print("="*80)
    
    playwright = None
    context = None
    
    try:
        # 启动浏览器
        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir="./deepseek_user_data",
            headless=False,
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("精准提取器已准备就绪")
        
        return {"status": "ready"}
        
    except Exception as e:
        print(f"❌ 执行过程中出错: {e}")
        return None
        
    finally:
        if context:
            await context.close()
        if playwright:
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main()) 