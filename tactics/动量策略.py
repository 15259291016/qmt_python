import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def parse_csv_file(file_path):
    """
    解析 CSV 文件为 DataFrame
    :param file_path: 文件路径
    :return: DataFrame
    """
    # 读取数据文件，假设 CSV 文件使用逗号作为分隔符
    df = pd.read_csv(file_path, sep=',')  # 使用逗号作为分隔符
    
    # 设置日期为索引
    df['日期'] = pd.to_datetime(df['日期'])
    df.set_index('日期', inplace=True)
    
    return df

def momentum_strategy_backtest(data_df, momentum_window=5, cost=0.0):
    """
    动量策略回测函数
    :param data_df: DataFrame, 数据
    :param momentum_window: int, 动量窗口长度（默认为 5 个交易日）
    :param cost: float, 交易成本（默认为 0）
    :return: None
    """
    df = data_df.copy()
    # 计算每日收益率
    df['收益率'] = df['收盘'].pct_change()

    # 计算动量指标
    df['动量'] = df['收益率'].rolling(window=momentum_window).sum()

    # 生成交易信号
    df['信号'] = np.where(df['动量'] > 0, 1, 0)

    # 计算持仓
    df['持仓'] = df['信号'].shift(1).fillna(0)

    # 计算策略收益
    df['策略收益'] = df['持仓'] * df['收益率'] * (1 - cost)  # 扣除交易成本

    # 计算累计收益率
    df['策略累计收益率'] = (1 + df['策略收益']).cumprod()
    df['股票累计收益率'] = (1 + df['收益率']).cumprod()

    # 可视化结果
    plt.figure(figsize=(12, 6))
    plt.plot(df['策略累计收益率'], label='动量策略累计收益率', color='blue')
    plt.plot(df['股票累计收益率'], label='股票累计收益率', color='red')
    plt.title('动量策略回测结果')
    plt.xlabel('日期')
    plt.ylabel('累计收益率')
    plt.legend()
    plt.grid(True)
    plt.show()

    # 输出动态买卖信号
    print("动态买卖信号:")
    return df[['收盘', '信号']].tail(10)

# 调用示例
df = parse_csv_file('algo/tactics/000001.csv')  # 假设文件路径为 '000001.csv'
result = momentum_strategy_backtest(df, momentum_window=5, cost=0.001)
print(result)