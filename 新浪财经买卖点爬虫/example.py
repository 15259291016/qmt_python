#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
买卖点爬虫使用示例
"""

import os
import sys
from dotenv import load_dotenv
from main import BuySellPointCrawler, StockCodeConverter

# 添加项目根目录到路径（如果需要导入项目其他模块）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def example_crawl_method():
    """示例：使用爬取方法（方案1）"""
    print("=" * 60)
    print("示例1: 直接爬取新浪财经买卖点数据")
    print("=" * 60)
    
    crawler = BuySellPointCrawler(method='crawl')
    stock_code = '603444'  # 吉比特
    
    print(f"\n正在爬取股票 {stock_code} 的买卖点数据...")
    result = crawler.get_buy_sell_points(stock_code)
    
    if result:
        print(f"\n爬取成功！")
        print(f"股票代码: {result.get('stock_code', 'N/A')}")
        print(f"买入点数量: {len(result.get('buy_points', []))}")
        print(f"卖出点数量: {len(result.get('sell_points', []))}")
        
        if result.get('buy_points'):
            print("\n买入点:")
            for point in result['buy_points'][:5]:  # 显示前5个
                print(f"  {point}")
        
        if result.get('sell_points'):
            print("\n卖出点:")
            for point in result['sell_points'][:5]:  # 显示前5个
                print(f"  {point}")
    else:
        print("\n爬取失败，建议使用计算方法（方案2）")


def example_calculate_method():
    """示例：使用计算方法（方案2，推荐）"""
    print("\n" + "=" * 60)
    print("示例2: 自行计算买卖点指标（推荐）")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    
    if not tushare_token:
        print("\n警告: 未找到TUSHARE_TOKEN，将尝试使用AKShare数据源")
    
    crawler = BuySellPointCrawler(method='calculate', tushare_token=tushare_token)
    stock_code = '603444'  # 吉比特
    
    print(f"\n正在计算股票 {stock_code} 的买卖点...")
    result = crawler.get_buy_sell_points(stock_code, days=250)
    
    if 'error' in result:
        print(f"\n错误: {result['error']}")
        return
    
    print(f"\n计算完成！")
    print(f"股票代码: {result.get('stock_code', 'N/A')}")
    print(f"计算方法: {result.get('method', 'N/A')}")
    print(f"计算时间: {result.get('calculate_time', 'N/A')}")
    print(f"买入点数量: {result.get('total_buy_points', 0)}")
    print(f"卖出点数量: {result.get('total_sell_points', 0)}")
    
    if result.get('buy_points'):
        print(f"\n最近5个买入点:")
        for point in result['buy_points'][-5:]:
            score = point.get('score', 0)
            strength = point.get('strength', '')
            rsi = point.get('rsi', 'N/A')
            print(f"  日期: {point['date']}, 价格: {point['price']:.2f}, "
                  f"评分: {score:.2f}, 强度: {strength}, RSI: {rsi}")
    
    if result.get('sell_points'):
        print(f"\n最近5个卖出点:")
        for point in result['sell_points'][-5:]:
            score = point.get('score', 0)
            strength = point.get('strength', '')
            rsi = point.get('rsi', 'N/A')
            print(f"  日期: {point['date']}, 价格: {point['price']:.2f}, "
                  f"评分: {score:.2f}, 强度: {strength}, RSI: {rsi}")
    
    # 显示平均评分
    if result.get('avg_buy_score', 0) > 0:
        print(f"\n平均买入信号评分: {result['avg_buy_score']:.2f}")
    if result.get('avg_sell_score', 0) > 0:
        print(f"平均卖出信号评分: {result['avg_sell_score']:.2f}")
    
    # 保存结果
    filename = f"买卖点_{stock_code}.csv"
    crawler.save_to_csv(result, filename)
    print(f"\n数据已保存到: {filename}")


def example_batch_process():
    """示例：批量处理多只股票"""
    print("\n" + "=" * 60)
    print("示例3: 批量处理多只股票")
    print("=" * 60)
    
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    
    crawler = BuySellPointCrawler(method='calculate', tushare_token=tushare_token)
    
    # 股票代码列表
    stock_codes = ['603444', '000001', '600000']
    
    results = []
    for stock_code in stock_codes:
        print(f"\n处理股票: {stock_code}")
        try:
            result = crawler.get_buy_sell_points(stock_code, days=250)
            if 'error' not in result:
                results.append(result)
                print(f"  买入点: {result.get('total_buy_points', 0)}, "
                      f"卖出点: {result.get('total_sell_points', 0)}")
            else:
                print(f"  错误: {result['error']}")
        except Exception as e:
            print(f"  处理失败: {e}")
    
    print(f"\n批量处理完成，成功处理 {len(results)} 只股票")


def example_custom_strategy():
    """示例：自定义买卖点策略（优化版）"""
    print("\n" + "=" * 60)
    print("示例4: 自定义买卖点策略（优化版）")
    print("=" * 60)
    
    from main import BuySellPointCalculator, StockDataFetcher
    
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    
    # 自定义参数：更严格的策略
    calculator = BuySellPointCalculator(
        ma_short=5,
        ma_mid=10,
        ma_long=20,
        ma_trend=60,
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        boll_period=20,
        boll_std=2.0,
        kdj_period=9,
        volume_ma_period=5,
        min_signal_score=3.0,          # 提高阈值，更严格
        min_days_between_signals=5     # 增加间隔，减少频繁交易
    )
    
    # 获取数据
    data_fetcher = StockDataFetcher(tushare_token)
    stock_code = '603444'
    df = data_fetcher.fetch_from_tushare(stock_code, days=250)
    
    if df is None or df.empty:
        df = data_fetcher.fetch_from_akshare(stock_code, days=250)
    
    if df is not None and not df.empty:
        # 计算买卖点
        df_with_signals = calculator.calculate_buy_sell_points(df)
        
        # 获取摘要
        summary = calculator.get_buy_sell_points_summary(df_with_signals)
        
        print(f"\n股票代码: {stock_code}")
        print(f"策略参数: 最小评分={calculator.min_signal_score}, "
              f"最小间隔={calculator.min_days_between_signals}天")
        print(f"买入点数量: {summary['total_buy_points']}")
        print(f"卖出点数量: {summary['total_sell_points']}")
        print(f"平均买入评分: {summary.get('avg_buy_score', 0):.2f}")
        print(f"平均卖出评分: {summary.get('avg_sell_score', 0):.2f}")
        
        # 显示强信号
        strong_buy = [p for p in summary.get('buy_points', []) if p.get('strength') == '强']
        strong_sell = [p for p in summary.get('sell_points', []) if p.get('strength') == '强']
        
        if strong_buy:
            print(f"\n强买入信号数量: {len(strong_buy)}")
            for point in strong_buy[-3:]:
                print(f"  {point['date']}: 价格={point['price']:.2f}, 评分={point['score']:.2f}")
        
        if strong_sell:
            print(f"\n强卖出信号数量: {len(strong_sell)}")
            for point in strong_sell[-3:]:
                print(f"  {point['date']}: 价格={point['price']:.2f}, 评分={point['score']:.2f}")
        
        print("\n提示: 可以通过调整 min_signal_score 和 min_days_between_signals 参数")
        print("      来平衡信号质量和数量")


if __name__ == '__main__':
    # 运行所有示例
    try:
        # 示例1: 爬取方法（可能不稳定）
        example_crawl_method()
        
        # 示例2: 计算方法（推荐）
        example_calculate_method()
        
        # 示例3: 批量处理
        # example_batch_process()
        
        # 示例4: 自定义策略
        # example_custom_strategy()
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
