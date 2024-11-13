# https://www.xiaohongshu.com/explore
import uvicorn
from fastapi import FastAPI
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By


app = FastAPI()

option = webdriver.ChromeOptions()
# 指定为无界面模式
# option.add_argument('--headless')
# option.add_argument("--disable-javascript")

prefs = {
    'profile.default_content_setting_values': {
        'images': 2,
        'javascript': 2
    }
}
option.add_experimental_option('prefs', prefs)
browser = webdriver.Chrome(options=option)
def get_xhs():
    url = "https://www.xiaohongshu.com/"
    browser.get(url)
    print(browser.get_cookies())
    browser.execute_script("window.onload=function(){}")
    # sleep(5)  #等待网页加载
    sleep(1)
    # element = browser.find_element(By.CLASS_NAME, 'reds-icon')
    # element.click()
    # element = browser.find_element(By.ID, 'homefeed_recommend')
    # element.click()
    element = browser.find_element(By.ID, 'exploreFeeds')

    res = [i.get_dom_attribute('href') for i in element.find_elements(By.CLASS_NAME, "cover")]
    print(res)
    return res

@app.get("/xhs")
async def root():
    data = get_xhs()
    return {"data": data}


if __name__ == '__main__':
    uvicorn.run("demo:app", host="0.0.0.0", port=8000, log_level="info")

