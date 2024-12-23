import pandas as pd
csv_file_path = './algo/find_code_demos/tushare项目/data/基础数据/股票列表.csv'    # 替换为您的CSV文件路径
df = pd.read_csv(csv_file_path)

def stock_names_to_list(stock_names:list[str]):
    return [i.split(".")[0] for i in df['ts_code'][df['name'].isin(stock_names)].tolist()]


if __name__ == '__main__':
    stock_names = ['平安银行', '万科A', '中兴通讯']
    print(stock_names_to_list(stock_names))