import pandas as pd
import numpy as np
import akshare as ak
from scipy.stats import linregress
from typing import List, Tuple
import os
import matplotlib.pyplot as plt

# ===================== 参数配置 =====================
SYMBOL = 'sz002594'  # 比亚迪A股代码
START_DATE = '20250101'
END_DATE = '20250725'
WINDOW = 5
SLOPE_THRESH = 0.02
THRESHOLD = 0.01  # 突破幅度阈值
INIT_CASH = 100000  # 初始资金
FEE_RATE = 0.001  # 手续费率（单边0.1%）

# ===================== 功能函数 =====================
def get_kline_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    获取A股日K线数据
    """
    try:
        df = ak.stock_zh_a_daily(symbol=symbol, start_date=start, end_date=end)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        return pd.DataFrame()

def find_local_extrema(series: pd.Series, window: int = 5, mode: str = 'max') -> List[int]:
    idxs = []
    for i in range(window, len(series) - window):
        segment = series[i - window:i + window + 1]
        if mode == 'max' and series[i] == max(segment):
            idxs.append(i)
        elif mode == 'min' and series[i] == min(segment):
            idxs.append(i)
    return idxs

def fit_trend_line(idxs: List[int], values: np.ndarray) -> Tuple[float, float]:
    if len(idxs) < 2:
        return 0.0, values[0] if len(values) > 0 else 0.0
    x = np.array(idxs)
    y = values
    slope, intercept, *_ = linregress(x, y)
    return slope, intercept

def detect_triangle_type(slope_high: float, slope_low: float, slope_thresh: float = 0.02) -> str:
    if slope_high < 0 and slope_low > 0:
        return "对称三角形"
    elif abs(slope_high) < slope_thresh and slope_low > slope_thresh:
        return "上升三角形"
    elif abs(slope_low) < slope_thresh and slope_high < -slope_thresh:
        return "下降三角形"
    else:
        return "未形成三角形"

def check_breakout(close: float, upper: float, lower: float, threshold: float = 0.01) -> str:
    if close > upper * (1 + threshold):
        return "上轨突破"
    elif close < lower * (1 - threshold):
        return "下轨突破"
    else:
        return "未突破"

def generate_trade_signal(breakout_result: str) -> str:
    if breakout_result == "上轨突破":
        return "买入"
    elif breakout_result == "下轨突破":
        return "卖出"
    else:
        return "观望"

# ===================== 回测主流程 =====================
def backtest_triangle_breakout(window=WINDOW, threshold=THRESHOLD, verbose=True, save_plot=False):
    df = get_kline_data(SYMBOL, START_DATE, END_DATE)
    if df.empty:
        if verbose:
            print("数据获取失败或数据为空！")
        return 0, []
    cash = INIT_CASH
    position = 0
    trade_log = []
    holding = False
    equity_curve = []  # 资金曲线
    for i in range(window*2, len(df)):
        window_df = df.iloc[:i+1]
        high_idxs = find_local_extrema(window_df['high'], window=window, mode='max')
        low_idxs = find_local_extrema(window_df['low'], window=window, mode='min')
        slope_high, intercept_high = fit_trend_line(high_idxs, window_df['high'].iloc[high_idxs].values)
        slope_low, intercept_low = fit_trend_line(low_idxs, window_df['low'].iloc[low_idxs].values)
        x = np.arange(len(window_df))
        upper_line = slope_high * x + intercept_high
        lower_line = slope_low * x + intercept_low
        close = window_df['close'].iloc[-1]
        upper = upper_line[-1]
        lower = lower_line[-1]
        breakout_result = check_breakout(close, upper, lower, threshold)
        signal = generate_trade_signal(breakout_result)
        date = window_df.index[-1]
        price = close
        if signal == '买入' and not holding:
            position = int(cash // price)
            cost = position * price * (1 + FEE_RATE)
            cash -= cost
            holding = True
            trade_log.append({'date': date, 'price': price, 'signal': '买入', 'position': position, 'cash': cash})
        elif signal == '卖出' and holding:
            proceeds = position * price * (1 - FEE_RATE)
            cash += proceeds
            trade_log.append({'date': date, 'price': price, 'signal': '卖出', 'position': 0, 'cash': cash})
            position = 0
            holding = False
        # 记录每日总资产
        total_value = cash + position * price if holding else cash
        equity_curve.append({'date': date, 'equity': total_value})
    final_value = cash + position * df['close'].iloc[-1] if holding else cash
    profit = final_value - INIT_CASH
    profit_rate = profit / INIT_CASH * 100
    if save_plot and equity_curve:
        # 资金曲线可视化
        eq_df = pd.DataFrame(equity_curve)
        plt.figure(figsize=(10, 5))
        plt.plot(eq_df['date'], eq_df['equity'], label='资金曲线')
        plt.xlabel('日期')
        plt.ylabel('总资产')
        plt.title(f'资金曲线 WINDOW={window} THRESHOLD={threshold:.3f}')
        plt.grid(True)
        plt.tight_layout()
        # 保存图片
        plot_path = os.path.join(os.path.dirname(__file__), f'equity_curve_WINDOW{window}_THRESHOLD{threshold:.3f}.png')
        plt.savefig(plot_path)
        plt.close()
    if verbose:
        print(f"\n参数: WINDOW={window}, THRESHOLD={threshold}")
        print(f"期末总资产：{final_value:.2f} 元，总收益率：{profit_rate:.2f}%")
    return profit_rate, trade_log

# ========== 参数自动优化主流程 ==========
def parameter_optimization():
    window_list = [3, 5, 7, 10]
    threshold_list = [0.005, 0.01, 0.015, 0.02]
    best_profit = -float('inf')
    best_params = None
    results = []
    print("正在自动优化参数，请稍候...\n")
    for window in window_list:
        for threshold in threshold_list:
            profit_rate, trade_log = backtest_triangle_breakout(window=window, threshold=threshold, verbose=False, save_plot=True)
            results.append({'window': window, 'threshold': threshold, 'profit_rate': profit_rate})
            # 保存每组参数的详细交易记录
            trade_log_df = pd.DataFrame(trade_log)
            trade_log_path = os.path.join(os.path.dirname(__file__), f'trade_log_WINDOW{window}_THRESHOLD{threshold:.3f}.csv')
            trade_log_df.to_csv(trade_log_path, index=False, encoding='utf-8-sig')
            if profit_rate > best_profit:
                best_profit = profit_rate
                best_params = (window, threshold)
    print("参数优化结果：")
    for r in results:
        print(f"WINDOW={r['window']}, THRESHOLD={r['threshold']:.3f} -> 收益率: {r['profit_rate']:.2f}%")
    print(f"\n最优参数: WINDOW={best_params[0]}, THRESHOLD={best_params[1]:.3f}，历史收益率最高为 {best_profit:.2f}%")
    # 保存优化结果到CSV
    results_df = pd.DataFrame(results)
    save_path = os.path.join(os.path.dirname(__file__), 'triangle_param_optimization_results.csv')
    results_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n所有参数优化结果已保存到: {save_path}")
    print(f"每组参数的详细交易记录已分别保存为 trade_log_WINDOW*_THRESHOLD*.csv 文件。")
    print(f"每组参数的资金曲线图已分别保存为 equity_curve_WINDOW*_THRESHOLD*.png 文件。")
    # 可选：用最优参数跑一次详细回测
    print("\n最优参数详细回测：")
    backtest_triangle_breakout(window=best_params[0], threshold=best_params[1], verbose=True, save_plot=True)

if __name__ == "__main__":
    # backtest_triangle_breakout()  # 注释掉单次回测
    parameter_optimization()  # 启动参数自动优化 