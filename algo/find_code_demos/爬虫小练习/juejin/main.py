# v2.0
# -*- coding: utf-8 -*-
import requests
import time



def check_sign_in_status(base_url, headers):
    api = "get_today_status"
    url = base_url + api
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data['err_no'] == 0:
            if data['data'] is True:
                print("【今日是否签到】", "已签到")
                return True
            elif data['data'] is False:
                print("【今日是否签到】", "未签到")
                return False
        else:
            print("【当前登录状态】", "未登录,请登录")
            pass
            return False
    else:
        print("【请求失败】", response.status_code)
        return False


def sign_in(base_url, params, headers):
    data = '{}'
    url = f"{base_url}check_in"
    response = requests.post(url, headers=headers, data=data,params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            if data['err_no'] == 0 and data['err_msg'] == "success":
                print("【当前签到状态】", "签到成功")
                return True
            elif data['err_no'] == 3013 and data['err_msg'] == "掘金酱提示：签到失败了~":
                print("【当前签到状态】", data['err_msg'])
                return False
            elif data['err_no'] == 15001:
                print("【当前签到状态】", '重复签到')
                return True
            else:
                print("【当前签到状态】", data['err_msg'])
                return False
        except requests.JSONDecodeError:
            print("【签到功能】服务器返回的数据无法解析为JSON格式。")
            return False


def get_points(base_url, headers):
    api = "get_cur_point"
    url = base_url + api
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            if data['err_no'] == 0 and data['err_msg'] == "success":
                print("【矿石最新余额】", data['data'])
                return data['data']
        except requests.JSONDecodeError:
            print("【获取余额功能】服务器返回的数据无法解析为JSON格式。")
            return False


def get_free(base_url,params, headers):
    url = f"{base_url}lottery_config/get"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            if data['err_no'] == 0 and data['err_msg'] == "success":
                if data['data']['free_count'] > 0:
                    print("【免费抽奖次数】", data['data']['free_count'])
                    return True
                else:
                    print("【免费抽奖次数】", data['data']['free_count'])
                    return False
        except requests.JSONDecodeError:
            print("【获取免费抽奖次数功能】服务器返回的数据无法解析为JSON格式。")
            return False


def draw(base_url, params, headers):
    # proxies = {
    # 'http': 'http://127.0.0.1:8080',
    # 'https': 'http://127.0.0.1:8080',
    # }
    url = f"{base_url}lottery/draw"
    data = '{}'
    response = requests.post(url, headers=headers, data=data,params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            if data['err_no'] == 0 and data['err_msg'] == "success":
                print("【今日抽奖奖品】", data['data']['lottery_name'])
        except requests.JSONDecodeError:
            print("【抽奖功能】服务器返回的数据无法解析为JSON格式。")
            return False


def get_win(base_url, aid, uuid, spider, headers):
    api = "lottery_lucky/my_lucky"
    url = base_url + api
    data = {
        "aid": aid,
        "uuid": uuid,
        "spider": spider
    }
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        try:
            data = response.json()
            if data['err_no'] == 0 and data['err_msg'] == "success":
                total_value = data['data']['total_value']
                points = get_points(base_url, header1)
                cha = points - (6000 - total_value) * 20
                print("【当前幸运数值】：", total_value)
                if cha >= 0:
                    print("【距离中奖还差】：0 矿石！")
                elif cha <= 0:
                    print("【距离中奖还差】：", str(abs(cha)) + "矿石！")
        except requests.JSONDecodeError:
            print("【获取免费抽奖次数功能】服务器返回的数据无法解析为JSON格式。")
            return False
    else:
        print("【请求失败】", response.status_code)
        return False



if __name__ == "__main__":
    cookie = '__tea_cookie_tokens_2608=%257B%2522web_id%2522%253A%25227439629556196017714%2522%252C%2522user_unique_id%2522%253A%25227439629556196017714%2522%252C%2522timestamp%2522%253A1732173755221%257D; passport_csrf_token=2baab949ce38006f96f755cb3d26b03d; passport_csrf_token_default=2baab949ce38006f96f755cb3d26b03d; _tea_utm_cache_2608={%22utm_source%22:%22gold_browser_extension%22}; _tea_utm_cache_2018={%22utm_source%22:%22gold_browser_extension%22}; csrf_session_id=7d5b383ffa1d8a7b5a5a64141cb2a1b5; n_mh=g4moaPIXnhmg7DEUsArgwInFfw3uCSNyidNFSqBVmI0; passport_auth_status=33a737c9920f40597b1cac34c2fe1899%2C; passport_auth_status_ss=33a737c9920f40597b1cac34c2fe1899%2C; sid_guard=eeed8912f021539d604320c46f02a1c2%7C1735810618%7C31536000%7CFri%2C+02-Jan-2026+09%3A36%3A58+GMT; uid_tt=f76fff09c2d44daacd99e57b3dd584c3; uid_tt_ss=f76fff09c2d44daacd99e57b3dd584c3; sid_tt=eeed8912f021539d604320c46f02a1c2; sessionid=eeed8912f021539d604320c46f02a1c2; sessionid_ss=eeed8912f021539d604320c46f02a1c2; is_staff_user=false; sid_ucp_v1=1.0.0-KDM0YzJiM2FmY2U0YjRhZjM4OTgyYjEzNzk2Njg2N2NlOWRkOTdiZTcKFwiOuLDF4o3AAhC6vNm7BhiwFDgCQPEHGgJscSIgZWVlZDg5MTJmMDIxNTM5ZDYwNDMyMGM0NmYwMmExYzI; ssid_ucp_v1=1.0.0-KDM0YzJiM2FmY2U0YjRhZjM4OTgyYjEzNzk2Njg2N2NlOWRkOTdiZTcKFwiOuLDF4o3AAhC6vNm7BhiwFDgCQPEHGgJscSIgZWVlZDg5MTJmMDIxNTM5ZDYwNDMyMGM0NmYwMmExYzI; store-region=cn-fj; store-region-src=uid'
    aid = ""
    uuid = ""
    spider = ""
    # msToken  获取后测试 url解码和未解码 哪种可以使用
    msToken = ''
    a_bogus = ''
    base_url = "https://api.juejin.cn/growth_api/v1/"

    common_params = {"aid": aid, "uuid": uuid, "spider": spider, "msToken": msToken, "a_bogus": a_bogus}
    header1 = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.61 Chrome/126.0.6478.61 Not/A)Brand/8  Safari/537.36'
    }
    # proxies = {
    #     'http': 'http://127.0.0.1:8080',
    #     'https': 'http://127.0.0.1:8080',
    # }
    if check_sign_in_status(base_url, header1):
        if get_free(base_url,common_params, header1):
            draw(base_url,common_params, header1)
            pass
        else:
            pass
    else:
        if not sign_in(base_url, common_params, header1):
            sign_in(base_url, common_params, header1)
        if get_free(base_url,common_params, header1):
            draw(base_url, common_params, header1)
            pass
        else:
            pass
    get_win(base_url, aid, uuid, spider, header1)
