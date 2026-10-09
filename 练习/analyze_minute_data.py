import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_minute_data(file_path):
    """加载分钟级数据"""
    df = pd.read_csv(file_path)
    df['trade_time'] = pd.to_datetime(df['trade_time'])
    df.set_index('trade_time', inplace=True)
    return df

def analyze_data_quality(df, stock_name):
    """分析数据质量"""
    print(f"\n=== {stock_name} 数据质量分析 ===")
    print(f"数据时间范围: {df.index.min()} 到 {df.index.max()}")
    print(f"总记录数: {len(df)}")
    print(f"数据列: {list(df.columns)}")
    
    # 检查缺失值
    print(f"\n缺失值统计:")
    print(df.isnull().sum())
    
    # 检查异常值
    print(f"\n价格统计:")
    print(df[['open', 'high', 'low', 'close']].describe())
    
    # 检查成交量
    print(f"\n成交量统计:")
    print(df['vol'].describe())
    
    return df

def add_technical_features(df):
    """添加技术指标特征，包括压力位和支撑位"""
    # 价格变化率
    df['price_change'] = df['close'].pct_change()
    df['price_change_5'] = df['close'].pct_change(5)
    
    # 移动平均线
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    
    # 成交量指标
    df['volume_ma5'] = df['vol'].rolling(5).mean()
    df['volume_ratio'] = df['vol'] / df['volume_ma5']
    
    # 波动率
    df['volatility'] = df['price_change'].rolling(20).std()
    
    # 时间特征
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['day_of_week'] = df.index.dayofweek
    
    # 价格区间
    df['price_range'] = (df['high'] - df['low']) / df['close']
    
    # --- 支撑位与压力位 ---
    N = 20
    # 区间高低点法
    df['resistance'] = df['high'].rolling(N).max()
    df['support'] = df['low'].rolling(N).min()
    # 布林带
    df['mid'] = df['close'].rolling(N).mean()
    df['std'] = df['close'].rolling(N).std()
    df['upper'] = df['mid'] + 2 * df['std']
    df['lower'] = df['mid'] - 2 * df['std']
    
    return df

def visualize_data(df, stock_name):
    """可视化数据，包含压力位和支撑位"""
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle(f'{stock_name} 分钟级数据分析', fontsize=16)
    
    # 1. 价格走势+压力位/支撑位
    axes[0, 0].plot(df.index, df['close'], label='收盘价', alpha=0.7)
    axes[0, 0].plot(df.index, df['ma5'], label='5分钟均线', alpha=0.7)
    axes[0, 0].plot(df.index, df['ma20'], label='20分钟均线', alpha=0.7)
    axes[0, 0].plot(df.index, df['resistance'], label='压力位(20高)', color='red', linestyle='--', alpha=0.7)
    axes[0, 0].plot(df.index, df['support'], label='支撑位(20低)', color='green', linestyle='--', alpha=0.7)
    axes[0, 0].plot(df.index, df['upper'], label='布林带上轨', color='magenta', linestyle=':')
    axes[0, 0].plot(df.index, df['lower'], label='布林带下轨', color='cyan', linestyle=':')
    axes[0, 0].set_title('价格走势/压力位/支撑位')
    axes[0, 0].legend()
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # 2. 成交量
    axes[0, 1].bar(df.index, df['vol'], alpha=0.6, color='orange')
    axes[0, 1].set_title('成交量')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 3. 价格变化率分布
    axes[1, 0].hist(df['price_change'].dropna(), bins=50, alpha=0.7, color='green')
    axes[1, 0].set_title('价格变化率分布')
    axes[1, 0].axvline(x=0, color='red', linestyle='--', alpha=0.7)
    
    # 4. 波动率
    axes[1, 1].plot(df.index, df['volatility'], color='purple', alpha=0.7)
    axes[1, 1].set_title('波动率')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    # 5. 日内交易模式
    hourly_volume = df.groupby('hour')['vol'].mean()
    axes[2, 0].bar(hourly_volume.index, hourly_volume.values, alpha=0.7, color='blue')
    axes[2, 0].set_title('日内成交量模式')
    axes[2, 0].set_xlabel('小时')
    axes[2, 0].set_ylabel('平均成交量')
    
    # 6. 价格区间分布
    axes[2, 1].hist(df['price_range'].dropna(), bins=30, alpha=0.7, color='red')
    axes[2, 1].set_title('价格区间分布')
    
    plt.tight_layout()
    plt.savefig(f'data/min/{stock_name}_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def calculate_statistics(df, stock_name):
    """计算统计指标"""
    print(f"\n=== {stock_name} 统计指标 ===")
    
    # 基本统计
    total_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
    print(f"总收益率: {total_return:.2f}%")
    
    # 波动率
    daily_volatility = df['price_change'].std() * np.sqrt(240) * 100  # 年化波动率
    print(f"年化波动率: {daily_volatility:.2f}%")
    
    # 最大回撤
    cumulative = (1 + df['price_change']).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    print(f"最大回撤: {max_drawdown:.2f}%")
    
    # 夏普比率（假设无风险利率为3%）
    risk_free_rate = 0.03
    excess_return = total_return / 100 - risk_free_rate
    sharpe_ratio = excess_return / (daily_volatility / 100)
    print(f"夏普比率: {sharpe_ratio:.2f}")
    
    # 交易活跃度
    active_minutes = (df['vol'] > 0).sum()
    total_minutes = len(df)
    activity_ratio = active_minutes / total_minutes * 100
    print(f"交易活跃度: {activity_ratio:.2f}%")
    
    return {
        'total_return': total_return,
        'volatility': daily_volatility,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'activity_ratio': activity_ratio
    }

def select_daily_stock_pool(data_dir, date_str):
    """
    每日推荐股票池：筛选均线+MACD金叉信号的股票
    :param data_dir: 股票数据目录
    :param date_str: 推荐日期（如'2025-07-10'）
    :return: 推荐股票池DataFrame
    """
    stock_files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and '_1min_' in f]
    selected = []

    for file in stock_files:
        df = pd.read_csv(os.path.join(data_dir, file))
        if 'trade_time' not in df.columns:
            continue
        df['trade_time'] = pd.to_datetime(df['trade_time'])
        day_df = df[df['trade_time'].dt.date == pd.to_datetime(date_str).date()]
        if len(day_df) < 2:
            continue
        last_row = day_df.iloc[-1]
        prev_row = day_df.iloc[-2]
        # 选股条件：均线金叉且MACD金叉
        if all(col in day_df.columns for col in ['ma5', 'ma20', 'DIF', 'DEA']):
            golden_cross = (last_row['ma5'] > last_row['ma20']) and (prev_row['ma5'] <= prev_row['ma20'])
            macd_golden = (last_row['DIF'] > last_row['DEA']) and (prev_row['DIF'] <= prev_row['DEA'])
            if golden_cross and macd_golden:
                selected.append({
                    'ts_code': last_row['ts_code'] if 'ts_code' in last_row else file.split('_')[0],
                    'date': date_str,
                    'close': last_row['close'],
                    'signal': '均线+MACD金叉'
                })
    return pd.DataFrame(selected)

def main():
    """主函数"""
    # 检查数据目录
    data_dir = "data/min"
    if not os.path.exists(data_dir):
        print("数据目录不存在，请先运行下载脚本")
        return
    
    # 只分析原始分钟数据文件
    data_files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and '_1min_' in f]
    
    if not data_files:
        print("没有找到数据文件")
        return
    
    print(f"找到 {len(data_files)} 个数据文件")
    
    # 分析每个文件
    all_stats = {}
    
    for file_name in data_files:
        file_path = os.path.join(data_dir, file_name)
        stock_name = file_name.split('_')[0]
        
        print(f"\n正在分析 {stock_name}...")
        
        # 加载数据
        df = load_minute_data(file_path)
        
        # 数据质量分析
        df = analyze_data_quality(df, stock_name)
        
        # 添加技术指标
        df = add_technical_features(df)
        
        # 可视化
        visualize_data(df, stock_name)
        
        # 计算统计指标
        stats = calculate_statistics(df, stock_name)
        all_stats[stock_name] = stats
        
        # 保存处理后的数据
        processed_file = os.path.join(data_dir, f"{stock_name}_processed.csv")
        df.to_csv(processed_file)
        print(f"处理后的数据已保存到: {processed_file}")
    
    # 汇总统计
    print("\n" + "="*50)
    print("汇总统计")
    print("="*50)
    
    stats_df = pd.DataFrame(all_stats).T
    print(stats_df.round(2))
    
    # 保存汇总统计
    stats_df.to_csv(os.path.join(data_dir, 'summary_statistics.csv'))
    print(f"\n汇总统计已保存到: {os.path.join(data_dir, 'summary_statistics.csv')}")

    # === 每日推荐股票池 ===
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"\n正在生成 {today_str} 的每日推荐股票池...")
    pool = select_daily_stock_pool(data_dir, today_str)
    print(pool)
    pool_file = os.path.join(data_dir, f'daily_stock_pool_{today_str}.csv')
    pool.to_csv(pool_file, index=False)
    print(f"每日推荐股票池已保存到: {pool_file}")

if __name__ == "__main__":
    main() 