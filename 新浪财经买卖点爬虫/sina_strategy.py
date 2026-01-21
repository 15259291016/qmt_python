#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪财经风格买卖点计算器
基于葛兰碧八大法则（Granville's Eight Rules）实现
这是新浪财经等平台常用的买卖点计算方法

参考：葛兰碧八大法则
- B1-B4: 四个买入点
- S1-S4: 四个卖出点
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class SinaStyleBuySellCalculator:
    """
    新浪财经风格买卖点计算器
    基于葛兰碧八大法则
    """
    
    def __init__(self, ma_period: int = 20):
        """
        初始化计算器
        
        Args:
            ma_period: 均线周期（默认20日，新浪财经常用）
        """
        self.ma_period = ma_period
    
    def calculate_ma(self, prices: pd.Series, period: int = None) -> pd.Series:
        """计算移动平均线"""
        if period is None:
            period = self.ma_period
        return prices.rolling(window=period).mean()
    
    def calculate_buy_sell_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算买卖点（基于葛兰碧八大法则）
        
        葛兰碧八大法则说明：
        
        **买入点（B点）：**
        - B1: 均线由下降转为水平或上升，股价从均线下方突破均线
        - B2: 均线上扬，股价上涨后回撤但未跌破均线，随后继续上涨
        - B3: 均线上扬，股价跌破均线后再次上涨
        - B4: 股价急跌远离均线后反弹接近均线
        
        **卖出点（S点）：**
        - S1: 均线由上升转为水平或下降，股价从均线上方跌破均线
        - S2: 均线下弯，股价反弹未突破均线后继续下跌
        - S3: 均线下弯，股价反弹突破均线后再次下跌
        - S4: 股价急涨远离均线后回落接近均线
        
        Args:
            df: 包含 'date', 'open', 'high', 'low', 'close', 'volume' 列的DataFrame
        
        Returns:
            添加了买卖点标记的DataFrame
        """
        if df.empty or len(df) < self.ma_period + 5:
            logger.warning(f"数据不足，需要至少{self.ma_period + 5}条数据")
            return df
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date']) if 'date' in df.columns else df.index
        
        # 计算均线
        close_prices = df['close']
        df['ma'] = self.calculate_ma(close_prices, self.ma_period)
        
        # 计算均线斜率（用于判断均线趋势）
        df['ma_slope'] = df['ma'].diff()
        df['ma_trend'] = ''  # 'up', 'down', 'flat'
        df['ma_trend'] = df['ma_slope'].apply(
            lambda x: 'up' if x > 0 else ('down' if x < 0 else 'flat')
        )
        
        # 计算价格与均线的距离（百分比）
        df['price_ma_distance'] = ((df['close'] - df['ma']) / df['ma']) * 100
        
        # 初始化买卖点标记
        df['buy_point'] = 0
        df['sell_point'] = 0
        df['buy_type'] = ''  # B1, B2, B3, B4
        df['sell_type'] = ''  # S1, S2, S3, S4
        df['signal'] = ''
        
        # 计算买卖点
        for i in range(self.ma_period + 2, len(df)):
            current_price = df.iloc[i]['close']
            prev_price = df.iloc[i-1]['close']
            current_ma = df.iloc[i]['ma']
            prev_ma = df.iloc[i-1]['ma']
            prev2_ma = df.iloc[i-2]['ma'] if i >= 2 else None
            
            current_trend = df.iloc[i]['ma_trend']
            prev_trend = df.iloc[i-1]['ma_trend']
            
            price_ma_dist = df.iloc[i]['price_ma_distance']
            
            # ========== 买入点判断 ==========
            
            # B1: 均线由下降转为水平或上升，股价从均线下方突破均线
            if (prev_trend in ['down', 'flat'] and current_trend in ['up', 'flat'] and
                df.iloc[i-1]['close'] < df.iloc[i-1]['ma'] and
                current_price > current_ma):
                df.iloc[i, df.columns.get_loc('buy_point')] = 1
                df.iloc[i, df.columns.get_loc('buy_type')] = 'B1'
                df.iloc[i, df.columns.get_loc('signal')] = 'B'
            
            # B2: 均线上扬，股价上涨后回撤但未跌破均线，随后继续上涨
            elif (current_trend == 'up' and
                  df.iloc[i-2]['close'] > df.iloc[i-2]['ma'] if i >= 2 else False and
                  df.iloc[i-1]['close'] >= df.iloc[i-1]['ma'] and
                  current_price > prev_price and
                  current_price > current_ma):
                # 检查是否有回撤但未跌破
                if i >= 3:
                    recent_prices = [df.iloc[j]['close'] for j in range(max(0, i-5), i)]
                    recent_mas = [df.iloc[j]['ma'] for j in range(max(0, i-5), i)]
                    if len(recent_prices) >= 3:
                        # 有回撤但未跌破均线
                        min_recent_price = min(recent_prices[:-1])
                        min_recent_ma = min(recent_mas[:-1])
                        if min_recent_price >= min_recent_ma * 0.98:  # 允许小幅跌破（2%容差）
                            df.iloc[i, df.columns.get_loc('buy_point')] = 1
                            df.iloc[i, df.columns.get_loc('buy_type')] = 'B2'
                            df.iloc[i, df.columns.get_loc('signal')] = 'B'
            
            # B3: 均线上扬，股价跌破均线后再次上涨
            elif (current_trend == 'up' and
                  df.iloc[i-2]['close'] < df.iloc[i-2]['ma'] if i >= 2 else False and
                  current_price > current_ma and
                  current_price > prev_price):
                df.iloc[i, df.columns.get_loc('buy_point')] = 1
                df.iloc[i, df.columns.get_loc('buy_type')] = 'B3'
                df.iloc[i, df.columns.get_loc('signal')] = 'B'
            
            # B4: 股价急跌远离均线后反弹接近均线
            elif (price_ma_dist < -3 and  # 股价低于均线3%以上
                  df.iloc[i-1]['price_ma_distance'] < price_ma_dist and  # 距离在缩小（反弹）
                  current_price > prev_price):  # 价格上涨
                # 检查是否是急跌后的反弹
                if i >= 5:
                    recent_distances = [df.iloc[j]['price_ma_distance'] for j in range(max(0, i-5), i)]
                    min_distance = min(recent_distances[:-1]) if len(recent_distances) > 1 else 0
                    if min_distance < -5:  # 之前有急跌（超过5%）
                        df.iloc[i, df.columns.get_loc('buy_point')] = 1
                        df.iloc[i, df.columns.get_loc('buy_type')] = 'B4'
                        df.iloc[i, df.columns.get_loc('signal')] = 'B'
            
            # ========== 卖出点判断 ==========
            
            # S1: 均线由上升转为水平或下降，股价从均线上方跌破均线
            if (prev_trend in ['up', 'flat'] and current_trend in ['down', 'flat'] and
                df.iloc[i-1]['close'] > df.iloc[i-1]['ma'] and
                current_price < current_ma):
                df.iloc[i, df.columns.get_loc('sell_point')] = 1
                df.iloc[i, df.columns.get_loc('sell_type')] = 'S1'
                df.iloc[i, df.columns.get_loc('signal')] = 'S'
            
            # S2: 均线下弯，股价反弹未突破均线后继续下跌
            elif (current_trend == 'down' and
                  df.iloc[i-2]['close'] < df.iloc[i-2]['ma'] if i >= 2 else False and
                  df.iloc[i-1]['close'] <= df.iloc[i-1]['ma'] and
                  current_price < prev_price and
                  current_price < current_ma):
                # 检查是否有反弹但未突破
                if i >= 3:
                    recent_prices = [df.iloc[j]['close'] for j in range(max(0, i-5), i)]
                    recent_mas = [df.iloc[j]['ma'] for j in range(max(0, i-5), i)]
                    if len(recent_prices) >= 3:
                        # 有反弹但未突破均线
                        max_recent_price = max(recent_prices[:-1])
                        max_recent_ma = max(recent_mas[:-1])
                        if max_recent_price <= max_recent_ma * 1.02:  # 允许小幅突破（2%容差）
                            df.iloc[i, df.columns.get_loc('sell_point')] = 1
                            df.iloc[i, df.columns.get_loc('sell_type')] = 'S2'
                            df.iloc[i, df.columns.get_loc('signal')] = 'S'
            
            # S3: 均线下弯，股价反弹突破均线后再次下跌
            elif (current_trend == 'down' and
                  df.iloc[i-2]['close'] > df.iloc[i-2]['ma'] if i >= 2 else False and
                  current_price < current_ma and
                  current_price < prev_price):
                df.iloc[i, df.columns.get_loc('sell_point')] = 1
                df.iloc[i, df.columns.get_loc('sell_type')] = 'S3'
                df.iloc[i, df.columns.get_loc('signal')] = 'S'
            
            # S4: 股价急涨远离均线后回落接近均线
            elif (price_ma_dist > 3 and  # 股价高于均线3%以上
                  df.iloc[i-1]['price_ma_distance'] > price_ma_dist and  # 距离在缩小（回落）
                  current_price < prev_price):  # 价格下跌
                # 检查是否是急涨后的回落
                if i >= 5:
                    recent_distances = [df.iloc[j]['price_ma_distance'] for j in range(max(0, i-5), i)]
                    max_distance = max(recent_distances[:-1]) if len(recent_distances) > 1 else 0
                    if max_distance > 5:  # 之前有急涨（超过5%）
                        df.iloc[i, df.columns.get_loc('sell_point')] = 1
                        df.iloc[i, df.columns.get_loc('sell_type')] = 'S4'
                        df.iloc[i, df.columns.get_loc('signal')] = 'S'
        
        return df
    
    def get_buy_sell_points_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取买卖点摘要信息（配对版本）
        
        Args:
            df: 包含买卖点标记的DataFrame
        
        Returns:
            买卖点摘要字典（包含配对信息）
        """
        buy_points = df[df['buy_point'] == 1].copy()
        sell_points = df[df['sell_point'] == 1].copy()
        
        # 统计各类型买卖点
        buy_type_count = buy_points['buy_type'].value_counts().to_dict()
        sell_type_count = sell_points['sell_type'].value_counts().to_dict()
        
        # 配对买卖点（一买一卖）
        pairs = []
        buy_indices = buy_points.index.tolist()
        sell_indices = sell_points.index.tolist()
        
        i = 0  # 买入点索引
        j = 0  # 卖出点索引
        
        while i < len(buy_indices) and j < len(sell_indices):
            buy_idx = buy_indices[i]
            sell_idx = sell_indices[j]
            
            # 如果卖出点在买入点之前，跳过这个卖出点
            if sell_idx < buy_idx:
                j += 1
                continue
            
            # 找到买入点后的第一个卖出点
            buy_row = buy_points.loc[buy_idx]
            sell_row = sell_points.loc[sell_idx]
            
            # 计算收益
            buy_price = float(buy_row['close'])
            sell_price = float(sell_row['close'])
            profit = sell_price - buy_price
            profit_pct = (profit / buy_price) * 100
            
            # 计算持仓天数
            buy_date = buy_row['date'] if 'date' in buy_row else pd.Timestamp(buy_idx)
            sell_date = sell_row['date'] if 'date' in sell_row else pd.Timestamp(sell_idx)
            if isinstance(buy_date, str):
                buy_date = pd.to_datetime(buy_date)
            if isinstance(sell_date, str):
                sell_date = pd.to_datetime(sell_date)
            days_held = (sell_date - buy_date).days
            
            pairs.append({
                'pair_id': len(pairs) + 1,
                'buy': {
                    'date': buy_date.strftime('%Y-%m-%d') if hasattr(buy_date, 'strftime') else str(buy_date),
                    'price': buy_price,
                    'volume': float(buy_row['volume']) if 'volume' in buy_row else 0,
                    'type': str(buy_row['buy_type']),
                    'ma': float(buy_row['ma']) if 'ma' in buy_row and not pd.isna(buy_row['ma']) else None,
                    'distance': float(buy_row['price_ma_distance']) if 'price_ma_distance' in buy_row and not pd.isna(buy_row['price_ma_distance']) else None
                },
                'sell': {
                    'date': sell_date.strftime('%Y-%m-%d') if hasattr(sell_date, 'strftime') else str(sell_date),
                    'price': sell_price,
                    'volume': float(sell_row['volume']) if 'volume' in sell_row else 0,
                    'type': str(sell_row['sell_type']),
                    'ma': float(sell_row['ma']) if 'ma' in sell_row and not pd.isna(sell_row['ma']) else None,
                    'distance': float(sell_row['price_ma_distance']) if 'price_ma_distance' in sell_row and not pd.isna(sell_row['price_ma_distance']) else None
                },
                'profit': profit,
                'profit_pct': profit_pct,
                'days_held': days_held
            })
            
            # 移动到下一个买入点
            i += 1
            j += 1
        
        # 未配对的买入点（没有对应卖出点）
        unpaired_buys = []
        if i < len(buy_indices):
            for idx in buy_indices[i:]:
                row = buy_points.loc[idx]
                date = row['date'] if 'date' in row else pd.Timestamp(idx)
                if isinstance(date, str):
                    date = pd.to_datetime(date)
                unpaired_buys.append({
                    'date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date),
                    'price': float(row['close']),
                    'type': str(row['buy_type']),
                    'status': '未卖出'
                })
        
        # 未配对的卖出点（没有对应买入点）
        unpaired_sells = []
        if j < len(sell_indices):
            for idx in sell_indices[j:]:
                row = sell_points.loc[idx]
                date = row['date'] if 'date' in row else pd.Timestamp(idx)
                if isinstance(date, str):
                    date = pd.to_datetime(date)
                unpaired_sells.append({
                    'date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date),
                    'price': float(row['close']),
                    'type': str(row['sell_type']),
                    'status': '无买入点'
                })
        
        return {
            'total_buy_points': len(buy_points),
            'total_sell_points': len(sell_points),
            'total_pairs': len(pairs),
            'buy_type_count': buy_type_count,
            'sell_type_count': sell_type_count,
            'pairs': pairs,  # 配对的买卖点
            'unpaired_buys': unpaired_buys,  # 未配对的买入点
            'unpaired_sells': unpaired_sells,  # 未配对的卖出点
            # 保留原有格式以便兼容
            'buy_points': [
                {
                    'date': row['date'].strftime('%Y-%m-%d') if 'date' in row else str(row.name),
                    'price': float(row['close']),
                    'volume': float(row['volume']) if 'volume' in row else 0,
                    'type': str(row['buy_type']),
                    'ma': float(row['ma']) if 'ma' in row and not pd.isna(row['ma']) else None,
                    'distance': float(row['price_ma_distance']) if 'price_ma_distance' in row and not pd.isna(row['price_ma_distance']) else None
                }
                for _, row in buy_points.iterrows()
            ],
            'sell_points': [
                {
                    'date': row['date'].strftime('%Y-%m-%d') if 'date' in row else str(row.name),
                    'price': float(row['close']),
                    'volume': float(row['volume']) if 'volume' in row else 0,
                    'type': str(row['sell_type']),
                    'ma': float(row['ma']) if 'ma' in row and not pd.isna(row['ma']) else None,
                    'distance': float(row['price_ma_distance']) if 'price_ma_distance' in row and not pd.isna(row['price_ma_distance']) else None
                }
                for _, row in sell_points.iterrows()
            ]
        }


def print_buy_sell_points(stock_code: str, days: int = 250, tushare_token: str = None, 
                         strategy: str = 'sina'):
    """
    打印买卖点日期（单独函数）
    
    Args:
        stock_code: 股票代码
        days: 数据天数
        tushare_token: Tushare token
        strategy: 策略类型，'sina' 或 'optimized'
    """
    from main import BuySellPointCalculator, StockDataFetcher
    
    # 获取数据
    data_fetcher = StockDataFetcher(tushare_token)
    df = data_fetcher.fetch_from_tushare(stock_code, days)
    if df is None or df.empty:
        df = data_fetcher.fetch_from_akshare(stock_code, days)
    
    if df is None or df.empty:
        print("无法获取数据")
        return
    
    if strategy == 'sina':
        print(f"\n{'='*60}")
        print(f"新浪财经风格买卖点 - {stock_code}")
        print(f"{'='*60}")
        calculator = SinaStyleBuySellCalculator(ma_period=20)
        df_with_signals = calculator.calculate_buy_sell_points(df)
        summary = calculator.get_buy_sell_points_summary(df_with_signals)
        
        print(f"\n买入点数量: {summary['total_buy_points']}")
        print(f"卖出点数量: {summary['total_sell_points']}")
        print(f"配对数量: {summary['total_pairs']}")
        
        # 显示配对信息
        if summary['pairs']:
            print(f"\n配对买卖点（一买一卖）:")
            total_profit = 0
            win_count = 0
            for pair in summary['pairs']:
                profit_sign = "+" if pair['profit'] > 0 else ""
                profit_color = "✓" if pair['profit'] > 0 else "✗"
                if pair['profit'] > 0:
                    win_count += 1
                total_profit += pair['profit']
                
                print(f"  {pair['pair_id']}. 买入: {pair['buy']['date']} @ {pair['buy']['price']:.2f} ({pair['buy']['type']}) "
                      f"→ 卖出: {pair['sell']['date']} @ {pair['sell']['price']:.2f} ({pair['sell']['type']}) "
                      f"收益: {profit_sign}{pair['profit_pct']:.2f}% [{profit_color}] ({pair['days_held']}天)")
            
            if summary['pairs']:
                win_rate = (win_count / len(summary['pairs'])) * 100
                avg_profit = total_profit / len(summary['pairs'])
                print(f"\n统计: 总收益={total_profit:.2f}, 平均收益={avg_profit:.2f}, 胜率={win_rate:.1f}% ({win_count}/{len(summary['pairs'])})")
        
        # 显示未配对的点
        if summary.get('unpaired_buys'):
            print(f"\n未配对的买入点: {len(summary['unpaired_buys'])}个")
            for point in summary['unpaired_buys']:
                print(f"  {point['date']} @ {point['price']:.2f} ({point['type']})")
        
        if summary.get('unpaired_sells'):
            print(f"\n未配对的卖出点: {len(summary['unpaired_sells'])}个")
            for point in summary['unpaired_sells']:
                print(f"  {point['date']} @ {point['price']:.2f} ({point['type']})")
    
    else:  # optimized
        print(f"\n{'='*60}")
        print(f"优化策略买卖点 - {stock_code}")
        print(f"{'='*60}")
        calculator = BuySellPointCalculator()
        df_with_signals = calculator.calculate_buy_sell_points(df)
        summary = calculator.get_buy_sell_points_summary(df_with_signals)
        
        print(f"\n买入点数量: {summary['total_buy_points']}")
        if summary.get('buy_points'):
            print(f"\n买入点日期列表:")
            for i, point in enumerate(summary['buy_points'], 1):
                score = point.get('score', 0)
                strength = point.get('strength', '')
                print(f"  {i}. {point['date']} - 价格: {point['price']:.2f}, "
                      f"评分: {score:.2f}, 强度: {strength}")
        
        print(f"\n卖出点数量: {summary['total_sell_points']}")
        if summary.get('sell_points'):
            print(f"\n卖出点日期列表:")
            for i, point in enumerate(summary['sell_points'], 1):
                score = point.get('score', 0)
                strength = point.get('strength', '')
                print(f"  {i}. {point['date']} - 价格: {point['price']:.2f}, "
                      f"评分: {score:.2f}, 强度: {strength}")


def compare_strategies(stock_code: str, days: int = 250, tushare_token: str = None):
    """
    对比新浪财经风格策略和优化策略
    
    Args:
        stock_code: 股票代码
        days: 数据天数
        tushare_token: Tushare token
    """
    from main import BuySellPointCalculator, StockDataFetcher
    
    print("=" * 60)
    print(f"策略对比: {stock_code}")
    print("=" * 60)
    
    # 获取数据
    data_fetcher = StockDataFetcher(tushare_token)
    df = data_fetcher.fetch_from_tushare(stock_code, days)
    if df is None or df.empty:
        df = data_fetcher.fetch_from_akshare(stock_code, days)
    
    if df is None or df.empty:
        print("无法获取数据")
        return
    
    # 策略1: 新浪财经风格（葛兰碧八大法则）
    print("\n【策略1】新浪财经风格（葛兰碧八大法则）")
    print("-" * 60)
    sina_calc = SinaStyleBuySellCalculator(ma_period=20)
    df_sina = sina_calc.calculate_buy_sell_points(df)
    sina_summary = sina_calc.get_buy_sell_points_summary(df_sina)
    
    print(f"买入点数量: {sina_summary['total_buy_points']}")
    print(f"卖出点数量: {sina_summary['total_sell_points']}")
    print(f"配对数量: {sina_summary['total_pairs']}")
    print(f"买入点类型分布: {sina_summary['buy_type_count']}")
    print(f"卖出点类型分布: {sina_summary['sell_type_count']}")
    
    # 打印配对的买卖点
    if sina_summary['pairs']:
        print(f"\n配对买卖点详情（一买一卖）:")
        total_profit = 0
        win_count = 0
        for pair in sina_summary['pairs']:
            profit_sign = "+" if pair['profit'] > 0 else ""
            profit_color = "盈利" if pair['profit'] > 0 else "亏损"
            if pair['profit'] > 0:
                win_count += 1
            total_profit += pair['profit']
            
            print(f"\n  配对 {pair['pair_id']}:")
            print(f"    买入: {pair['buy']['date']} @ {pair['buy']['price']:.2f} ({pair['buy']['type']})")
            print(f"    卖出: {pair['sell']['date']} @ {pair['sell']['price']:.2f} ({pair['sell']['type']})")
            print(f"    收益: {profit_sign}{pair['profit']:.2f} ({profit_sign}{pair['profit_pct']:.2f}%) [{profit_color}]")
            print(f"    持仓: {pair['days_held']} 天")
        
        if sina_summary['pairs']:
            win_rate = (win_count / len(sina_summary['pairs'])) * 100
            avg_profit = total_profit / len(sina_summary['pairs'])
            print(f"\n  统计:")
            print(f"    总收益: {total_profit:.2f}")
            print(f"    平均收益: {avg_profit:.2f}")
            print(f"    胜率: {win_rate:.2f}% ({win_count}/{len(sina_summary['pairs'])})")
    
    # 打印未配对的点
    if sina_summary.get('unpaired_buys'):
        print(f"\n未配对的买入点（{len(sina_summary['unpaired_buys'])}个）:")
        for point in sina_summary['unpaired_buys']:
            print(f"  {point['date']} @ {point['price']:.2f} ({point['type']}) - {point['status']}")
    
    if sina_summary.get('unpaired_sells'):
        print(f"\n未配对的卖出点（{len(sina_summary['unpaired_sells'])}个）:")
        for point in sina_summary['unpaired_sells']:
            print(f"  {point['date']} @ {point['price']:.2f} ({point['type']}) - {point['status']}")
    
    # 策略2: 优化策略（多指标综合）
    print("\n【策略2】优化策略（多指标综合评分）")
    print("-" * 60)
    opt_calc = BuySellPointCalculator()
    df_opt = opt_calc.calculate_buy_sell_points(df)
    opt_summary = opt_calc.get_buy_sell_points_summary(df_opt)
    
    print(f"买入点数量: {opt_summary['total_buy_points']}")
    print(f"卖出点数量: {opt_summary['total_sell_points']}")
    print(f"平均买入评分: {opt_summary.get('avg_buy_score', 0):.2f}")
    print(f"平均卖出评分: {opt_summary.get('avg_sell_score', 0):.2f}")
    
    # 打印买入点日期
    if opt_summary.get('buy_points'):
        print(f"\n买入点详情:")
        for i, point in enumerate(opt_summary['buy_points'], 1):
            score = point.get('score', 0)
            strength = point.get('strength', '')
            rsi = point.get('rsi', 'N/A')
            rsi_str = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else str(rsi)
            print(f"  {i}. 日期: {point['date']}, 价格: {point['price']:.2f}, "
                  f"评分: {score:.2f}, 强度: {strength}, RSI: {rsi_str}")
    
    # 打印卖出点日期
    if opt_summary.get('sell_points'):
        print(f"\n卖出点详情:")
        for i, point in enumerate(opt_summary['sell_points'], 1):
            score = point.get('score', 0)
            strength = point.get('strength', '')
            rsi = point.get('rsi', 'N/A')
            rsi_str = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else str(rsi)
            print(f"  {i}. 日期: {point['date']}, 价格: {point['price']:.2f}, "
                  f"评分: {score:.2f}, 强度: {strength}, RSI: {rsi_str}")
    
    # 对比结果
    print("\n【对比总结】")
    print("-" * 60)
    print(f"{'指标':<20} {'新浪风格':<15} {'优化策略':<15}")
    print("-" * 60)
    print(f"{'买入点数量':<20} {sina_summary['total_buy_points']:<15} {opt_summary['total_buy_points']:<15}")
    print(f"{'卖出点数量':<20} {sina_summary['total_sell_points']:<15} {opt_summary['total_sell_points']:<15}")


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    
    # 默认运行对比策略（会打印买卖点日期）
    compare_strategies('603444', days=250, tushare_token=tushare_token)
    
    # 如果需要单独打印新浪财经风格的买卖点日期，可以使用：
    # print_buy_sell_points('603444', days=250, tushare_token=tushare_token, strategy='sina')
    
    # 如果需要单独打印优化策略的买卖点日期，可以使用：
    # print_buy_sell_points('603444', days=250, tushare_token=tushare_token, strategy='optimized')
