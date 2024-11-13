import pandas as pd
import requests as req
import time
def jsl_output_newstock_data():
    t = str(int(time.time() * 1000))
    'pageurl=https://www.jisilu.cn/data/new_stock/#apply'
    url = f'https://www.jisilu.cn/data/new_stock/apply/?___jsl=LST___t={t}'
    # print(url)
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'origin': 'https://www.jisilu.cn',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded'
    }
    pddata = pd.DataFrame()
    datalist = []
    outputfile = 'jsl_newstock.csv'
    j = 0
    for i in range(4):
        body = f'rp=22&page={i}&pageSize=100&market=bj'
        # print(body)
        try:
            resp = req.post(url=url, headers=headers, data=body, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                rows = data['rows']
                print(f'本次取到数据{len(rows)}条')
                if len(rows) > 0:
                    for i in range(len(rows)):
                        cell = rows[i]['cell']
                        datalist.append(cell)
                        j += 1
                        # print(j,cell)
                else:
                    continue
            else:
                print(resp.content.decode('utf-8'))
        except BaseException as b:
            # print(b)
            continue
    if len(datalist) > 0:
        pddata = pd.DataFrame(datalist)
        # print(len(pddata.columns),pddata.columns)
        columns = ['代码', '名称', '注册', 'apply_dt', 'stock_check_dt', 'need_market_value', '申购代码', '发行价',
                   'above_rt', '发行pe', '行业pe', '申购限额(万股)', 'jsl_advise', '中签率', 'list_dt', '收益率',
                   'final_data', '开板收盘价', 'single_draw_money', 'general_capital', 'overall_amt', 'strategy_amt',
                   '承销商', '招股章程', '招股说明书', 'money_ava_dt', 'jsl_need_market_value', 'jsl_issue_price',
                   'jsl_issue_price_notes', 'eval_amt', 'real_online_amt', 'jsl_individual_limit',
                   'individual_limit_money', 'jsl_individual_limit_money', 'issue_amt', 'online_amt',
                   'jsl_theory_price', '发行时总市值亿', '公开发行市值亿', '市场', '单签收益', '申购日期', '缴款日期',
                   'money_out_dt', '上市日期', 'need_market_value_show', 'issue_price_show', 'individual_limit_show',
                   'individual_limit_money_show']

        pddata.columns = columns
        print('共取到数据：', len(pddata))
        pddata.drop_duplicates(subset=['代码'], keep='first', inplace=True)
        pddata.drop_duplicates(subset=['申购代码'], keep='first', inplace=True)
        print('去重后数据：', len(pddata))
        pddata.sort_values(by='申购日期', ascending=False, inplace=True)
        pddata.reset_index(drop=True, inplace=True)
        pddata1 = pddata[
            ['代码', '名称', '申购日期', 'stock_check_dt', '申购代码', '发行价', '发行pe', '行业pe', '申购限额(万股)',
             '中签率', '收益率', '单签收益', '上市日期', '开板收盘价', '承销商', '招股章程', '招股说明书',
             '发行时总市值亿', '公开发行市值亿', '市场']]

        pddata1.to_csv(outputfile, index=False)


if __name__ == '__main__':
    jsl_output_newstock_data()
