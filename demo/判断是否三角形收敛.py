
import pandas as pd
import numpy as np
import mplfinance as mpf
from scipy.stats import linregress
import matplotlib.pyplot as plt
import akshare as ak
import matplotlib.font_manager as fm
from typing import List, Tuple

# ===================== 参数配置 =====================
SYMBOL = 'sz002082'
START_DATE = '20250101'
END_DATE = '20250725'
WINDOW = 5
FONT_PATH = 'C:/Windows/Fonts/simhei.ttf'  # 可根据实际情况修改
SLOPE_THRESH = 0.02

# ===================== 功能函数 =====================
def get_kline_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    获取A股日K线数据
    """
    try:
        df = ak.stock_zh_a_daily(symbol=symbol, start_date=start, end_date=end)
        return df
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        return pd.DataFrame()

def find_local_extrema(series: pd.Series, window: int = 5, mode: str = 'max') -> List[int]:
    """
    查找局部极值点索引
    """
    idxs = []
    for i in range(window, len(series) - window):
        segment = series[i - window:i + window + 1]
        if mode == 'max' and series[i] == max(segment):
            idxs.append(i)
        elif mode == 'min' and series[i] == min(segment):
            idxs.append(i)
    return idxs

def fit_trend_line(idxs: List[int], values: np.ndarray) -> Tuple[float, float]:
    """
    用线性回归拟合趋势线，返回斜率和截距
    """
    if len(idxs) < 2:
        return 0.0, values[0] if len(values) > 0 else 0.0
    x = np.array(idxs)
    y = values
    slope, intercept, *_ = linregress(x, y)
    return slope, intercept

def detect_triangle_type(slope_high: float, slope_low: float, slope_thresh: float = 0.02) -> str:
    """
    判断三角形形态类型
    """
    if slope_high < 0 and slope_low > 0:
        return "对称三角形"
    elif abs(slope_high) < slope_thresh and slope_low > slope_thresh:
        return "上升三角形"
    elif abs(slope_low) < slope_thresh and slope_high < -slope_thresh:
        return "下降三角形"
    else:
        return "未形成三角形"

def plot_kline_with_triangle(df: pd.DataFrame, upper_line: np.ndarray, lower_line: np.ndarray, triangle_type: str, font_path: str):
    """
    绘制K线图及三角形收敛线
    """
    try:
        my_font = fm.FontProperties(fname=font_path)
        font_name = my_font.get_name()
    except Exception as e:
        print(f"字体加载失败: {e}，将使用默认字体。")
        font_name = 'sans-serif'
    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False
    my_style = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.family': font_name})
    apds = [
        mpf.make_addplot(upper_line, color='red', linestyle='--'),
        mpf.make_addplot(lower_line, color='red', linestyle='--')
    ]
    title_text = f'K线三角形态识别：{triangle_type}'
    mpf.plot(df, 
             type='candle', 
             style=my_style,
             addplot=apds, 
             title=title_text,
             ylabel='Price',
             figsize=(12, 6))

def check_breakout(df: pd.DataFrame, upper_line: np.ndarray, lower_line: np.ndarray, threshold: float = 0.01) -> str:
    """
    判断是否发生突破
    :param df: K线数据，index为日期
    :param upper_line: 上边界线
    :param lower_line: 下边界线
    :param threshold: 突破幅度阈值（如0.01表示1%）
    :return: '上轨突破'、'下轨突破'或'未突破'
    """
    last_idx = -1  # 最后一根K线
    close = df['close'].iloc[last_idx]
    upper = upper_line[last_idx]
    lower = lower_line[last_idx]
    if close > upper * (1 + threshold):
        return "上轨突破"
    elif close < lower * (1 - threshold):
        return "下轨突破"
    else:
        return "未突破"

def generate_trade_signal(breakout_result: str) -> str:
    """
    根据突破结果生成买入/卖出信号
    :param breakout_result: '上轨突破'、'下轨突破'或'未突破'
    :return: '买入'、'卖出'或'观望'
    """
    if breakout_result == "上轨突破":
        return "买入"
    elif breakout_result == "下轨突破":
        return "卖出"
    else:
        return "观望"

# ===================== 主流程 =====================
def main():
    # 1. 获取K线数据
    df = get_kline_data(SYMBOL, START_DATE, END_DATE)
    if df.empty or 'date' not in df.columns:
        print("数据获取失败或数据为空！")
        return
    # 2. 数据预处理，设置索引
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    # 3. 查找极值点
    high_idxs = find_local_extrema(df['high'], window=WINDOW, mode='max')
    low_idxs = find_local_extrema(df['low'], window=WINDOW, mode='min')
    # 4. 趋势线拟合
    slope_high, intercept_high = fit_trend_line(high_idxs, df['high'].iloc[high_idxs].values)
    slope_low, intercept_low = fit_trend_line(low_idxs, df['low'].iloc[low_idxs].values)
    # 5. 形态识别
    triangle_type = detect_triangle_type(slope_high, slope_low, SLOPE_THRESH)
    print("识别结果：", triangle_type)
    # 6. 构造趋势线
    x = np.arange(len(df))
    upper_line = slope_high * x + intercept_high
    lower_line = slope_low * x + intercept_low
    # 7. 绘图
    plot_kline_with_triangle(df, upper_line, lower_line, triangle_type, FONT_PATH)
    # 8. 判断是否突破
    breakout_result = check_breakout(df, upper_line, lower_line)
    print("突破判断：", breakout_result)
    # 9. 生成交易信号
    trade_signal = generate_trade_signal(breakout_result)
    print("交易信号：", trade_signal)

if __name__ == "__main__":
    main() 