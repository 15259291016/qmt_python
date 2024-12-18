from queue import Queue
from DrissionPage import ChromiumPage, ChromiumOptions
from threading import Thread
import time
co = ChromiumOptions().auto_port()  # 指定程序每次使用空闲的端口和临时用户文件夹创建浏览器
co.headless(True)  # 无头模式
co.set_argument('--no-sandbox')  # 无沙盒模式
co.set_argument('--headless=new')  # 无界面系统添加
co.set_paths(browser_path="/usr/bin/google-chrome")  # 设置浏览器路径
page = ChromiumPage(co)
page.get("https://www.xiazaitool.com/dy")
tab1 = page.get_tab()
q = Queue()
res = dict()
tab1('x://html/body/div[1]/nav/div/div/ul[2]/li[1]/a').click('js')  # 简化写法
jym = tab1.ele('#verifyImg', timeout=5).src
jym_str = ""
while jym_str == "":
    jym_str = str(jym).split(" ")[8][5:-1]
    print(jym_str)
    time.sleep(1)
a = input("请输入一个值:")
print(a)

tab1.ele("#account").input("19026045487")
tab1.ele("#password").input("6116988.niu")
tab1.ele("#imgCode").input(a)
tab1.ele("#get_login").click('js')
def consumer(tab1, q):
    while True:
        word_list = q.get()
        time.sleep(0.5)
        tab1.ele("#urlInput").input(word_list)
        # tab1.wait.load_start()  # 等待页面进入加载状态
        tab1.ele("#downloadButton").click('js')
        tab1.wait.load_start()  # 等待页面进入加载状态
        # time.sleep(10)
        source = tab1.ele('tag:source')
        res["a"] = source.attr("src")
        print(res["a"])
        time.sleep(10)

Thread(target=consumer, args=(tab1,q)).start()

q.put("5.38 复制打开抖音，看看【草帽小子yyds的作品】相应国家号召 做小做新做科技做重组 onepiec... https://v.douyin.com/iDs54kV6/ aNW:/ 04/13 X@Z.mQ ")