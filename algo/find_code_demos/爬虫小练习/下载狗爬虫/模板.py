from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions().auto_port()  # 指定程序每次使用空闲的端口和临时用户文件夹创建浏览器
co.headless(True)  # 无头模式
co.set_argument('--no-sandbox')  # 无沙盒模式
co.set_argument('--headless=new')  # 无界面系统添加
co.set_paths(browser_path="/usr/bin/google-chrome")  # 设置浏览器路径
page = ChromiumPage(co)
page.get("https://www.xiazaitool.com/dy")
print(page.title)
