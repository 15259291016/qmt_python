#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
买卖点功能验证脚本
用于测试和验证买卖点计算功能的正确性和有效性
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Any
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import BuySellPointCrawler, BuySellPointCalculator, StockDataFetcher


class BuySellPointVerifier:
    """买卖点验证器"""
    
    def __init__(self, tushare_token: str = None):
        """
        初始化验证器
        
        Args:
            tushare_token: Tushare API token
        """
        self.tushare_token = tushare_token
        self.crawler = BuySellPointCrawler(method='calculate', tushare_token=tushare_token)
        self.data_fetcher = StockDataFetcher(tushare_token)
    
    def verify_single_stock(self, stock_code: str, days: int = 250) -> Dict[str, Any]:
        """
        验证单只股票的买卖点
        
        Args:
            stock_code: 股票代码
            days: 数据天数
        
        Returns:
            验证结果字典
        """
        print(f"\n{'='*60}")
        print(f"验证股票: {stock_code}")
        print(f"{'='*60}")
        
        # 获取买卖点数据
        result = self.crawler.get_buy_sell_points(stock_code, days)
        
        if 'error' in result:
            print(f"❌ 错误: {result['error']}")
            return {'success': False, 'error': result['error']}
        
        # 显示基本信息
        print(f"\n📊 基本信息:")
        print(f"  股票代码: {result['stock_code']}")
        print(f"  计算方法: {result.get('method', 'calculate')}")
        print(f"  计算时间: {result.get('calculate_time', 'N/A')}")
        print(f"  买入点数量: {result['total_buy_points']}")
        print(f"  卖出点数量: {result['total_sell_points']}")
        
        if result.get('avg_buy_score', 0) > 0:
            print(f"  平均买入评分: {result['avg_buy_score']:.2f}")
        if result.get('avg_sell_score', 0) > 0:
            print(f"  平均卖出评分: {result['avg_sell_score']:.2f}")
        
        # 显示买卖点详情
        if result.get('buy_points'):
            print(f"\n📈 买入点详情 (共{len(result['buy_points'])}个):")
            for i, point in enumerate(result['buy_points'][-10:], 1):  # 显示最近10个
                score = point.get('score', 0)
                strength = point.get('strength', '')
                rsi = point.get('rsi', 'N/A')
                rsi_str = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else str(rsi)
                print(f"  {i}. {point['date']}: 价格={point['price']:.2f}, "
                      f"评分={score:.2f}, 强度={strength}, RSI={rsi_str}")
        
        if result.get('sell_points'):
            print(f"\n📉 卖出点详情 (共{len(result['sell_points'])}个):")
            for i, point in enumerate(result['sell_points'][-10:], 1):  # 显示最近10个
                score = point.get('score', 0)
                strength = point.get('strength', '')
                rsi = point.get('rsi', 'N/A')
                rsi_str = f"{rsi:.1f}" if isinstance(rsi, (int, float)) else str(rsi)
                print(f"  {i}. {point['date']}: 价格={point['price']:.2f}, "
                      f"评分={score:.2f}, 强度={strength}, RSI={rsi_str}")
        
        # 验证数据质量
        validation = self._validate_result(result)
        print(f"\n✅ 数据质量验证:")
        for key, value in validation.items():
            status = "✓" if value else "✗"
            print(f"  {status} {key}: {value}")
        
        return {
            'success': True,
            'result': result,
            'validation': validation
        }
    
    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, bool]:
        """
        验证结果数据质量
        
        Args:
            result: 买卖点结果
        
        Returns:
            验证结果字典
        """
        validation = {}
        
        # 检查是否有买卖点
        validation['有买入点'] = result.get('total_buy_points', 0) > 0
        validation['有卖出点'] = result.get('total_sell_points', 0) > 0
        
        # 检查评分是否合理
        buy_points = result.get('buy_points', [])
        sell_points = result.get('sell_points', [])
        
        if buy_points:
            buy_scores = [p.get('score', 0) for p in buy_points]
            validation['买入评分合理'] = all(2.0 <= s <= 6.0 for s in buy_scores)
            validation['买入评分有差异'] = max(buy_scores) - min(buy_scores) > 0.5 if len(buy_scores) > 1 else True
        
        if sell_points:
            sell_scores = [p.get('score', 0) for p in sell_points]
            validation['卖出评分合理'] = all(2.0 <= s <= 6.0 for s in sell_scores)
            validation['卖出评分有差异'] = max(sell_scores) - min(sell_scores) > 0.5 if len(sell_scores) > 1 else True
        
        # 检查信号强度分布
        if buy_points:
            strengths = [p.get('strength', '') for p in buy_points]
            validation['买入信号强度分布'] = len(set(strengths)) > 0
        
        if sell_points:
            strengths = [p.get('strength', '') for p in sell_points]
            validation['卖出信号强度分布'] = len(set(strengths)) > 0
        
        return validation
    
    def backtest_strategy(self, stock_code: str, days: int = 250, 
                         initial_capital: float = 100000) -> Dict[str, Any]:
        """
        回测买卖点策略
        
        Args:
            stock_code: 股票代码
            days: 数据天数
            initial_capital: 初始资金
        
        Returns:
            回测结果字典
        """
        print(f"\n{'='*60}")
        print(f"回测策略: {stock_code}")
        print(f"{'='*60}")
        
        # 获取历史数据
        df = self.data_fetcher.fetch_from_tushare(stock_code, days)
        if df is None or df.empty:
            df = self.data_fetcher.fetch_from_akshare(stock_code, days)
        
        if df is None or df.empty:
            return {'success': False, 'error': '无法获取数据'}
        
        # 计算买卖点
        calculator = BuySellPointCalculator()
        df_with_signals = calculator.calculate_buy_sell_points(df)
        
        # 执行回测
        capital = initial_capital
        position = 0  # 持仓数量
        buy_price = 0
        trades = []
        equity_curve = []
        
        for i, row in df_with_signals.iterrows():
            date = row['date'] if 'date' in row else i
            price = row['close']
            
            # 买入信号
            if row['buy_point'] == 1 and position == 0:
                # 全仓买入
                position = capital / price
                buy_price = price
                capital = 0
                trades.append({
                    'date': date,
                    'type': 'buy',
                    'price': price,
                    'shares': position,
                    'score': row.get('buy_score', 0),
                    'strength': row.get('signal_strength', '')
                })
            
            # 卖出信号
            elif row['sell_point'] == 1 and position > 0:
                # 全仓卖出
                capital = position * price
                profit = capital - (position * buy_price)
                profit_pct = (profit / (position * buy_price)) * 100
                position = 0
                trades.append({
                    'date': date,
                    'type': 'sell',
                    'price': price,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'score': row.get('sell_score', 0),
                    'strength': row.get('signal_strength', '')
                })
            
            # 记录权益曲线
            current_value = capital + (position * price) if position > 0 else capital
            equity_curve.append({
                'date': date,
                'value': current_value,
                'price': price
            })
        
        # 计算最终结果
        final_value = capital + (position * df_with_signals.iloc[-1]['close']) if position > 0 else capital
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # 计算统计指标
        buy_trades = [t for t in trades if t['type'] == 'buy']
        sell_trades = [t for t in trades if t['type'] == 'sell']
        
        win_trades = [t for t in sell_trades if t['profit'] > 0]
        loss_trades = [t for t in sell_trades if t['profit'] <= 0]
        
        win_rate = (len(win_trades) / len(sell_trades) * 100) if sell_trades else 0
        avg_profit = np.mean([t['profit_pct'] for t in sell_trades]) if sell_trades else 0
        avg_win = np.mean([t['profit_pct'] for t in win_trades]) if win_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in loss_trades]) if loss_trades else 0
        
        # 计算最大回撤
        equity_values = [e['value'] for e in equity_curve]
        max_drawdown = self._calculate_max_drawdown(equity_values)
        
        # 计算基准收益（买入持有）
        buy_hold_return = ((df_with_signals.iloc[-1]['close'] - df_with_signals.iloc[0]['close']) 
                          / df_with_signals.iloc[0]['close']) * 100
        
        # 显示结果
        print(f"\n💰 回测结果:")
        print(f"  初始资金: {initial_capital:,.2f}")
        print(f"  最终资金: {final_value:,.2f}")
        print(f"  总收益率: {total_return:.2f}%")
        print(f"  基准收益(买入持有): {buy_hold_return:.2f}%")
        print(f"  最大回撤: {max_drawdown:.2f}%")
        
        print(f"\n📊 交易统计:")
        print(f"  买入次数: {len(buy_trades)}")
        print(f"  卖出次数: {len(sell_trades)}")
        print(f"  胜率: {win_rate:.2f}%")
        print(f"  平均收益: {avg_profit:.2f}%")
        print(f"  平均盈利: {avg_win:.2f}%")
        print(f"  平均亏损: {avg_loss:.2f}%")
        
        if sell_trades:
            print(f"\n📈 最近5次交易:")
            for i, trade in enumerate(sell_trades[-5:], 1):
                profit_str = f"+{trade['profit_pct']:.2f}%" if trade['profit'] > 0 else f"{trade['profit_pct']:.2f}%"
                print(f"  {i}. {trade['date']}: {trade['type']} @ {trade['price']:.2f}, "
                      f"收益={profit_str}, 评分={trade['score']:.2f}, 强度={trade['strength']}")
        
        return {
            'success': True,
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'trades': trades,
            'equity_curve': equity_curve
        }
    
    def _calculate_max_drawdown(self, equity_values: List[float]) -> float:
        """计算最大回撤"""
        if not equity_values:
            return 0.0
        
        peak = equity_values[0]
        max_dd = 0.0
        
        for value in equity_values:
            if value > peak:
                peak = value
            dd = ((peak - value) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def compare_strategies(self, stock_code: str, days: int = 250):
        """
        比较不同参数策略的表现
        
        Args:
            stock_code: 股票代码
            days: 数据天数
        """
        print(f"\n{'='*60}")
        print(f"策略对比: {stock_code}")
        print(f"{'='*60}")
        
        strategies = [
            {'name': '保守策略', 'min_score': 3.5, 'min_days': 5},
            {'name': '平衡策略', 'min_score': 2.5, 'min_days': 3},
            {'name': '激进策略', 'min_score': 2.0, 'min_days': 2},
        ]
        
        results = []
        for strategy in strategies:
            print(f"\n测试 {strategy['name']}...")
            calculator = BuySellPointCalculator(
                min_signal_score=strategy['min_score'],
                min_days_between_signals=strategy['min_days']
            )
            
            df = self.data_fetcher.fetch_from_tushare(stock_code, days)
            if df is None or df.empty:
                df = self.data_fetcher.fetch_from_akshare(stock_code, days)
            
            if df is None or df.empty:
                continue
            
            df_with_signals = calculator.calculate_buy_sell_points(df)
            summary = calculator.get_buy_sell_points_summary(df_with_signals)
            
            results.append({
                'name': strategy['name'],
                'buy_points': summary['total_buy_points'],
                'sell_points': summary['total_sell_points'],
                'avg_buy_score': summary.get('avg_buy_score', 0),
                'avg_sell_score': summary.get('avg_sell_score', 0)
            })
        
        # 显示对比结果
        print(f"\n{'策略名称':<15} {'买入点':<10} {'卖出点':<10} {'平均买入评分':<15} {'平均卖出评分':<15}")
        print("-" * 70)
        for r in results:
            print(f"{r['name']:<15} {r['buy_points']:<10} {r['sell_points']:<10} "
                  f"{r['avg_buy_score']:<15.2f} {r['avg_sell_score']:<15.2f}")


def main():
    """主函数"""
    print("=" * 60)
    print("买卖点功能验证工具")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    
    if not tushare_token:
        print("\n⚠️  警告: 未找到TUSHARE_TOKEN，将尝试使用AKShare数据源")
    
    verifier = BuySellPointVerifier(tushare_token)
    
    # 测试股票列表
    test_stocks = ['603444', '000001', '600000']  # 吉比特、平安银行、浦发银行
    
    print("\n请选择验证模式:")
    print("1. 验证单只股票")
    print("2. 回测策略")
    print("3. 对比不同策略")
    print("4. 批量验证多只股票")
    
    try:
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            stock_code = input(f"请输入股票代码 (默认603444): ").strip() or '603444'
            verifier.verify_single_stock(stock_code, days=250)
        
        elif choice == '2':
            stock_code = input(f"请输入股票代码 (默认603444): ").strip() or '603444'
            verifier.backtest_strategy(stock_code, days=250, initial_capital=100000)
        
        elif choice == '3':
            stock_code = input(f"请输入股票代码 (默认603444): ").strip() or '603444'
            verifier.compare_strategies(stock_code, days=250)
        
        elif choice == '4':
            print(f"\n批量验证股票: {', '.join(test_stocks)}")
            for stock_code in test_stocks:
                try:
                    verifier.verify_single_stock(stock_code, days=250)
                except Exception as e:
                    print(f"❌ {stock_code} 验证失败: {e}")
        
        else:
            print("无效选项，运行默认验证...")
            verifier.verify_single_stock('603444', days=250)
    
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
