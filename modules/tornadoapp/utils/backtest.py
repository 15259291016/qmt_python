import pandas as pd

def backtest_signals(df, buy_col='buy_signal', sell_col='sell_signal', price_col='close', fee=0.001):
    """
    简单信号回测：每次买入信号全仓买，卖出信号全仓卖，统计收益
    :param df: DataFrame，需包含买卖信号列
    :param buy_col: 买入信号列名
    :param sell_col: 卖出信号列名
    :param price_col: 价格列名
    :param fee: 单边手续费率
    :return: 回测结果dict
    """
    position = 0
    entry_price = 0
    trades = []
    for i, row in df.iterrows():
        if position == 0 and row.get(buy_col, False):
            position = 1
            entry_price = row[price_col] * (1 + fee)
        elif position == 1 and row.get(sell_col, False):
            exit_price = row[price_col] * (1 - fee)
            ret = (exit_price - entry_price) / entry_price
            trades.append(ret)
            position = 0
    # 若最后持仓未平仓，按最后收盘价平仓
    if position == 1:
        exit_price = df[price_col].iloc[-1] * (1 - fee)
        ret = (exit_price - entry_price) / entry_price
        trades.append(ret)
    # 统计
    if trades:
        win_rate = sum([1 for r in trades if r > 0]) / len(trades)
        total_return = (1 + pd.Series(trades)).prod() - 1
        avg_return = pd.Series(trades).mean()
    else:
        win_rate = 0
        total_return = 0
        avg_return = 0
    return {
        'trades': len(trades),
        'win_rate': win_rate,
        'total_return': total_return,
        'avg_return': avg_return
    } 