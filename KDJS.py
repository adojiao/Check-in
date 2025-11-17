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

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # === 第一步：直接访问任务页面并设置Cookie ===
        task_url = "https://www.chinadsl.net/home.php?mod=task&do=view&id=1"
        driver.get("https://www.chinadsl.net/")  # 先访问首页设置Cookie
        
        # 设置Cookie
        cookies = cookie_str.split(';')
        for cookie in cookies:
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.chinadsl.net'
                })
        
        print("✓ Cookie设置完成")
        
        # === 第二步：访问任务页面 ===
        driver.get(task_url)
        print("已访问任务页面，等待立即申请按钮加载...")
        
        # 等待一段时间让页面加载
        time.sleep(10)

        # === 第三步：检查是否已登录 ===
        if "登录" in driver.page_source and "注册" in driver.page_source:
            print("❌ Cookie可能已失效，需要重新获取")
            return

        print("✓ 已通过Cookie登录")

        # === 第四步：查找并点击立即申请按钮 ===
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
                button_title = apply_button.get_attribute("title") or ""
                button_onclick = apply_button.get_attribute("onclick") or ""
                
                print(f"按钮标题: {button_title}")
                print(f"按钮onclick: {button_onclick}")
                
                # 检查按钮是否可用
                if "后可以再次申请" in button_title or "后可以再次申请" in button_onclick:
                    print("⏰ 任务已完成，下次可申请时间请查看按钮标题提示")
                    return
                
                # 尝试点击按钮
                driver.execute_script("arguments[0].scrollIntoView();", apply_button)
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
            # 检查页面是否有其他提示信息
            if "任务已完成" in driver.page_source:
                print("ℹ️ 页面提示任务已完成")
            elif "已申请" in driver.page_source:
                print("ℹ️ 页面提示已申请")

        # 保存截图用于调试
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"task_result_{timestamp}.png")
        print(f"已保存任务页面截图: task_result_{timestamp}.png")

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
