# KDJS.py
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    # 从环境变量读取Cookie
    cookie_str = os.getenv('CHINADSL_COOKIE')
    if not cookie_str:
        print("错误: 未设置Cookie环境变量。")
        return

    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    # 设置User-Agent，模拟真实浏览器
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # === 第一步：先访问网站根域名 ===
        print("正在访问网站首页...")
        driver.get("https://www.chinadsl.net/")
        time.sleep(3)
        
        # === 第二步：清除现有Cookie，然后设置新Cookie ===
        driver.delete_all_cookies()
        
        # 解析Cookie字符串并逐个设置
        cookies = cookie_str.split(';')
        for cookie in cookies:
            cookie = cookie.strip()
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                # 为每个Cookie设置完整的属性
                cookie_dict = {
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.chinadsl.net',
                    'path': '/',
                    'secure': False
                }
                try:
                    driver.add_cookie(cookie_dict)
                    print(f"✓ 设置Cookie: {name.strip()}")
                except Exception as e:
                    print(f"⚠️ 设置Cookie {name} 时出错: {e}")
        
        print("✓ Cookie设置完成")
        
        # === 第三步：刷新页面使Cookie生效 ===
        driver.refresh()
        time.sleep(3)
        
        # === 第四步：检查登录状态 ===
        print("检查登录状态...")
        
        # 方法1：检查页面是否包含登录相关元素
        page_source = driver.page_source
        if "退出" in page_source or "退出登录" in page_source or "我的空间" in page_source:
            print("✓ 登录状态验证成功")
        elif "登录" in page_source and "注册" in page_source:
            print("❌ 登录状态验证失败，仍显示登录注册链接")
            # 保存截图用于调试
            driver.save_screenshot("login_failed.png")
            return
        
        # 方法2：尝试访问用户中心页面
        print("访问用户中心验证登录状态...")
        driver.get("https://www.chinadsl.net/home.php?mod=space")
        time.sleep(3)
        
        if "登录" in driver.page_source and "注册" in driver.page_source:
            print("❌ 无法访问用户中心，Cookie可能已失效")
            driver.save_screenshot("cookie_invalid.png")
            return
        else:
            print("✓ 用户中心访问成功，登录状态正常")

        # === 第五步：访问任务页面 ===
        task_url = "https://www.chinadsl.net/home.php?mod=task&do=view&id=1"
        driver.get(task_url)
        print("已访问任务页面，等待立即申请按钮加载...")
        
        # 等待一段时间让页面加载
        time.sleep(10)

        # === 第六步：查找并点击立即申请按钮 ===
        print("查找立即申请按钮...")
        
        # 多种可能的选择器
        apply_selectors = [
            "a.taskbtn",  # 类选择器
            "a[onclick*='doane']",  # 包含特定onclick事件
            "a[title*='申请']",  # title属性包含"申请"
            "a:contains('立即申请')",  # 包含特定文本
        ]
        
        apply_button = None
        for selector in apply_selectors:
            try:
                apply_button = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✓ 找到立即申请按钮 - 使用选择器: {selector}")
                
                # 获取按钮状态信息
                button_text = apply_button.text
                button_title = apply_button.get_attribute("title") or ""
                button_onclick = apply_button.get_attribute("onclick") or ""
                
                print(f"按钮文本: {button_text}")
                print(f"按钮标题: {button_title}")
                print(f"按钮onclick: {button_onclick}")
                
                # 检查按钮是否可用
                if "后可以再次申请" in button_title or "后可以再次申请" in button_onclick:
                    print("⏰ 任务已完成，下次可申请时间请查看按钮标题提示")
                    return
                
                # 尝试点击按钮
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", apply_button)
                time.sleep(2)
                apply_button.click()
                print("✓ 已点击立即申请按钮")
                
                # 等待申请处理
                time.sleep(5)
                
                # 检查申请结果
                page_text = driver.page_source
                if "申请成功" in page_text or "任务完成" in page_text:
                    print("✅ 任务申请成功！")
                elif "已申请" in page_text or "已经申请" in page_text:
                    print("ℹ️ 今日已申请过该任务")
                else:
                    print("⚠️ 申请状态未知，请查看截图确认")
                
                break
                
            except Exception as e:
                print(f"✗ 选择器 {selector} 失败: {e}")
                continue
        
        if not apply_button:
            print("❌ 未找到立即申请按钮")
            # 保存当前页面截图和源代码用于调试
            driver.save_screenshot("no_button_found.png")
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("已保存页面截图和源代码用于调试")

        # 保存最终截图
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"final_result_{timestamp}.png")
        print(f"已保存最终截图: final_result_{timestamp}.png")

    except Exception as e:
        print(f"❌ 自动化过程出现错误: {str(e)}")
        # 出错时保存截图
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"error_{timestamp}.png")
        print(f"已保存错误截图: error_{timestamp}.png")
    finally:
        driver.quit()
        print("浏览器已关闭。")

if __name__ == "__main__":
    main()
