#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

class LoginManager:
    def __init__(self):
        self.state_file = "login_state.json"
        
    async def manual_login(self, website_name: str, url: str):
        """手动登录并保存登录状态"""
        print(f"=== {website_name} 手动登录 ===")
        print(f"正在打开 {url}")
        print("请在浏览器中完成以下步骤：")
        print("1. 完成人机验证（如果出现）")
        print("2. 输入账号密码登录")
        print("3. 确保进入聊天界面")
        print("4. 登录成功后按回车键继续...")
        
        try:
            playwright = await async_playwright().start()
            
            # 使用最简单的启动方式
            browser = await playwright.chromium.launch(headless=False)
            
            context = await browser.new_context()
            
            page = await context.new_page()
            page.set_default_timeout(60000)
            
            # 访问网站
            await page.goto(url, timeout=60000)
            
            # 等待用户完成验证和登录
            input("请完成人机验证和登录，然后按回车键继续...")
            
            # 再次确认是否已登录
            title = await page.title()
            print(f"当前页面标题: {title}")
            
            if "login" in title.lower() or "sign in" in title.lower():
                print("⚠ 看起来还在登录页面，请确保已成功登录")
                input("如果已登录，请按回车继续；如果未登录，请先登录再按回车...")
            
            # 保存登录状态
            await context.storage_state(path=self.state_file)
            print(f"✓ 登录状态已保存到 {self.state_file}")
            
            # 验证登录状态
            print("正在验证登录状态...")
            title = await page.title()
            print(f"当前页面标题: {title}")
            
            # 检查是否在聊天页面
            if "chat" in title.lower() or "openai" in title.lower():
                print("✓ 登录状态验证成功")
                
                # 尝试查找聊天输入框确认
                try:
                    chat_input = await page.wait_for_selector("textarea", timeout=10000)
                    if chat_input:
                        print("✓ 找到聊天输入框，登录完全成功")
                    else:
                        print("⚠ 未找到聊天输入框，但页面标题正确")
                except:
                    print("⚠ 未找到聊天输入框，但页面标题正确")
            else:
                print("⚠ 可能未正确登录，请检查")
            
            await context.close()
            await browser.close()
            await playwright.stop()
            
        except Exception as e:
            print(f"登录过程出错: {e}")
            if 'playwright' in locals():
                await playwright.stop()
    
    async def test_login_state(self, website_name: str, url: str):
        """测试登录状态是否有效"""
        print(f"=== 测试 {website_name} 登录状态 ===")
        
        if not os.path.exists(self.state_file):
            print(f"✗ 登录状态文件 {self.state_file} 不存在")
            return False
        
        try:
            playwright = await async_playwright().start()
            
            browser = await playwright.chromium.launch(headless=True)
            
            # 使用保存的登录状态
            context = await browser.new_context(storage_state=self.state_file)
            
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            # 访问网站
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 检查页面标题
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 针对不同网站进行检测
            if website_name == "DeepSeek":
                # DeepSeek 的检测逻辑
                if "deepseek" in title.lower():
                    print("✓ 登录状态有效，已进入 DeepSeek 页面")
                    
                    # 尝试查找聊天输入框
                    try:
                        chat_input = await page.wait_for_selector("textarea", timeout=10000)
                        if chat_input:
                            print("✓ 找到聊天输入框，登录状态完全有效")
                            await context.close()
                            await browser.close()
                            await playwright.stop()
                            return True
                        else:
                            print("✗ 未找到聊天输入框")
                    except Exception as e:
                        print(f"✗ 查找聊天输入框失败: {e}")
                        
                    # 尝试其他选择器
                    try:
                        chat_input = await page.wait_for_selector("[contenteditable='true']", timeout=5000)
                        if chat_input:
                            print("✓ 找到可编辑区域，登录状态有效")
                            await context.close()
                            await browser.close()
                            await playwright.stop()
                            return True
                    except:
                        pass
                        
                elif "login" in title.lower() or "sign in" in title.lower():
                    print("✗ 登录状态无效，仍在登录页面")
                else:
                    print("⚠ 页面状态不明确，但可能已登录")
                    
            elif website_name == "ChatGPT":
                # ChatGPT 的检测逻辑
                if "chat" in title.lower() or "openai" in title.lower():
                    print("✓ 登录状态有效，已进入聊天页面")
                    
                    # 尝试查找聊天输入框
                    try:
                        chat_input = await page.wait_for_selector("textarea", timeout=10000)
                        if chat_input:
                            print("✓ 找到聊天输入框，登录状态完全有效")
                            await context.close()
                            await browser.close()
                            await playwright.stop()
                            return True
                        else:
                            print("✗ 未找到聊天输入框")
                    except Exception as e:
                        print(f"✗ 查找聊天输入框失败: {e}")
                else:
                    print("✗ 登录状态无效，仍在登录页面")
            
            await context.close()
            await browser.close()
            await playwright.stop()
            return False
            
        except Exception as e:
            print(f"测试登录状态时出错: {e}")
            if 'playwright' in locals():
                await playwright.stop()
            return False
    
    def get_state_file(self):
        """获取登录状态文件路径"""
        return self.state_file if os.path.exists(self.state_file) else None

async def main():
    """主函数"""
    print("=== 登录态管理工具 ===")
    print("1. 手动登录 DeepSeek")
    print("2. 手动登录 ChatGPT")
    print("3. 测试登录状态")
    print("4. 查看登录状态文件")
    print("5. 删除登录状态文件")
    
    choice = input("\n请选择操作 (1-5): ").strip()
    
    manager = LoginManager()
    
    if choice == "1":
        await manager.manual_login("DeepSeek", "https://chat.deepseek.com")
    elif choice == "2":
        await manager.manual_login("ChatGPT", "https://chat.openai.com")
    elif choice == "3":
        print("选择要测试的网站：")
        print("1. DeepSeek")
        print("2. ChatGPT")
        site_choice = input("请选择 (1-2): ").strip()
        if site_choice == "1":
            await manager.test_login_state("DeepSeek", "https://chat.deepseek.com")
        elif site_choice == "2":
            await manager.test_login_state("ChatGPT", "https://chat.openai.com")
        else:
            print("无效的选择")
    elif choice == "4":
        state_file = manager.get_state_file()
        if state_file:
            print(f"登录状态文件: {state_file}")
            # 显示文件信息
            stat = os.stat(state_file)
            print(f"文件大小: {stat.st_size} 字节")
            print(f"创建时间: {datetime.fromtimestamp(stat.st_ctime)}")
        else:
            print("登录状态文件不存在")
    elif choice == "5":
        if os.path.exists(manager.state_file):
            os.remove(manager.state_file)
            print(f"✓ 已删除登录状态文件: {manager.state_file}")
        else:
            print("登录状态文件不存在")
    else:
        print("无效的选择")

if __name__ == "__main__":
    asyncio.run(main()) 