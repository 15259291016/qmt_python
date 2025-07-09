import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_atr(df, period=20):
    """
    计算平均真实范围 (ATR)
    """
    df['high_low'] = df['最高'] - df['最低']
    df['high_close'] = np.abs(df['最高'] - df['收盘'].shift())
    df['low_close'] = np.abs(df['最低'] - df['收盘'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr'] = df['tr'].rolling(window=period).mean()
    return df

def turtle_trading_strategy(data_file, n1=20, n2=55, risk_per_trade=0.02):
    """
    海龟交易系统实现
    :param data_file: 数据文件路径
    :param n1: 入市规则中的突破周期 (例如 20 日)
    :param n2: 入市规则中的突破周期 (例如 55 日)
    :param risk_per_trade: 每笔交易的风险比例 (例如 2%)
    """
    # 读取数据
    df = pd.read_csv(data_file, 
                     sep=',',  # 假设数据用逗号分隔
                     )
    
    # 将日期列转换为 datetime 类型
    df['日期'] = pd.to_datetime(df['日期'], format='%Y-%m-%d')  # 指定日期格式
    
    # 设置日期为索引
    df.set_index('日期', inplace=True)

    # 计算 ATR
    df = calculate_atr(df)

    # 计算突破指标
    df['price_high_n1'] = df['最高'].rolling(window=n1).max()
    df['price_low_n1'] = df['最低'].rolling(window=n1).min()
    df['price_high_n2'] = df['最高'].rolling(window=n2).max()
    df['price_low_n2'] = df['最低'].rolling(window=n2).min()

    # 初始化变量
    positions = []  # 持仓记录
    current_position = 0  # 当前持仓量
    entry_price = 0  # 入场价格
    exit_price = 0  # 止损价格
    current_units = 0  # 当前单位头寸
    atr = 0  # 当前 ATR

    # 初始化净值
    initial_equity = 100000  # 初始资金
    equity = [initial_equity]

    # 逐行回测
    for index, row in df.iterrows():
        # 计算当前 ATR
        atr = row['atr']

        # 如果没有持仓
        if current_position == 0:
            # 检查多头信号
            if row['收盘'] > df.loc[:index, 'price_high_n1'].max():
                # 计算单位头寸
                unit_size = (initial_equity * risk_per_trade) / (atr * 100)  # 假设每单位合约价值 100
                current_units = unit_size
                current_position = current_units
                entry_price = row['收盘']
                exit_price = entry_price - (2 * atr)

                # 记录持仓
                positions.append({'date': index, 'type': 'buy', 'price': row['收盘'], 'units': current_units})
            # 检查空头信号
            elif row['收盘'] < df.loc[:index, 'price_low_n1'].min():
                # 计算单位头寸
                unit_size = (initial_equity * risk_per_trade) / (atr * 100)
                current_units = -unit_size
                current_position = current_units
                entry_price = row['收盘']
                exit_price = entry_price + (2 * atr)

                # 记录持仓
                positions.append({'date': index, 'type': 'sell', 'price': row['收盘'], 'units': current_units})
        else:
            # 持有头寸
            if current_position > 0:
                # 检查止损信号
                if row['收盘'] < exit_price:
                    # 平仓
                    profit = (entry_price - row['收盘']) * current_units
                    initial_equity += profit
                    current_position = 0
                    entry_price = 0
                    current_units = 0

                    # 记录平仓
                    positions.append({'date': index, 'type': 'sell', 'price': row['收盘'], 'units': -current_units})
                # 检查加仓信号
                elif row['收盘'] > entry_price + (0.5 * atr):
                    # 计算单位头寸
                    unit_size = (initial_equity * risk_per_trade) / (atr * 100)
                    current_units += unit_size
                    current_position = current_units
                    # 更新止损价格
                    exit_price = row['收盘'] - (2 * atr)

                    # 记录加仓
                    positions.append({'date': index, 'type': 'buy', 'price': row['收盘'], 'units': unit_size})
            else:
                # 检查止损信号
                if row['收盘'] > exit_price:
                    # 平仓
                    profit = (row['收盘'] - entry_price) * current_units
                    initial_equity += profit
                    current_position = 0
                    entry_price = 0
                    current_units = 0

                    # 记录平仓
                    positions.append({'date': index, 'type': 'buy', 'price': row['收盘'], 'units': -current_units})
                # 检查加仓信号
                elif row['收盘'] < entry_price - (0.5 * atr):
                    # 计算单位头寸
                    unit_size = (initial_equity * risk_per_trade) / (atr * 100)
                    current_units -= unit_size
                    current_position = current_units
                    # 更新止损价格
                    exit_price = row['收盘'] + (2 * atr)

                    # 记录加仓
                    positions.append({'date': index, 'type': 'sell', 'price': row['收盘'], 'units': -current_units})

        # 更新净值
        equity.append(initial_equity)
    equity.pop()
    # 计算累计收益率
    df['equity'] = equity
    df['return'] = (df['equity'] - df['equity'].shift(1)) / df['equity'].shift(1)
    df['cumulative_return'] = (1 + df['return']).cumprod()

    # 绘制净值曲线
    plt.figure(figsize=(12, 6))
    plt.plot(df['equity'], label='净值曲线', color='blue')
    plt.title('海龟交易系统回测净值曲线')
    plt.xlabel('日期')
    plt.ylabel('净值')
    plt.legend()
    plt.grid(True)
    plt.show()

    # 输出持仓记录
    print("持仓记录:")
    for pos in positions:
        print(pos)

# 调用示例
turtle_trading_strategy('algo/tactics/000001.csv', n1=20, n2=55, risk_per_trade=0.02)