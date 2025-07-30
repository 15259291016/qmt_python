# coding=utf-8
"""
Backtrader 回测框架使用示例
展示如何使用新的 Backtrader 回测引擎
"""

import logging
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入 Backtrader 模块
from modules.backtrader_engine import (
    BacktraderEngine,
    MultiStrategyBacktestEngine,
    TushareDataFeed,
    MAStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    BacktestResultsAnalyzer
)


def run_single_strategy_backtest():
    """运行单策略回测示例"""
    logger.info("开始单策略回测示例")
    
    # 配置参数
    symbol = '000001.SZ'  # 平安银行
    start_date = '20230101'
    end_date = '20231231'
    tushare_token = 'your_tushare_token'  # 替换为你的 token
    
    try:
        # 1. 创建数据源
        data_feed = TushareDataFeed(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            tushare_token=tushare_token
        )
        
        # 2. 创建回测引擎
        engine = BacktraderEngine(
            initial_cash=1000000,
            commission=0.001,
            margin=0.0
        )
        
        # 3. 添加数据源
        engine.add_data(data_feed, name=symbol)
        
        # 4. 添加策略
        engine.add_strategy(MAStrategy, strategy_name='MA_Strategy')
        
        # 5. 运行回测
        result = engine.run_backtest('MA_Strategy')
        
        # 6. 生成报告
        report = engine.generate_report()
        print(report)
        
        # 7. 绘制结果
        engine.plot_results(filename='ma_strategy_results.png')
        
        # 8. 保存结果
        engine.save_results('ma_strategy_results.json')
        
        logger.info("单策略回测完成")
        
    except Exception as e:
        logger.error(f"单策略回测失败: {e}")


def run_multi_strategy_backtest():
    """运行多策略回测示例"""
    logger.info("开始多策略回测示例")
    
    # 配置参数
    symbols = ['000001.SZ', '000002.SZ', '000858.SZ']  # 平安银行、万科A、五粮液
    start_date = '20230101'
    end_date = '20231231'
    tushare_token = 'your_tushare_token'  # 替换为你的 token
    
    try:
        # 1. 创建多策略回测引擎
        multi_engine = MultiStrategyBacktestEngine(
            initial_cash=1000000,
            commission=0.001
        )
        
        # 2. 为每个股票添加不同的策略
        strategy_configs = [
            {
                'symbol': '000001.SZ',
                'strategy_class': MAStrategy,
                'strategy_name': 'MA_Strategy_000001',
                'strategy_params': {'short_window': 5, 'long_window': 20}
            },
            {
                'symbol': '000002.SZ',
                'strategy_class': RSIStrategy,
                'strategy_name': 'RSI_Strategy_000002',
                'strategy_params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70}
            },
            {
                'symbol': '000858.SZ',
                'strategy_class': MACDStrategy,
                'strategy_name': 'MACD_Strategy_000858',
                'strategy_params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
            }
        ]
        
        # 3. 添加策略回测
        for config in strategy_configs:
            # 创建数据源
            data_feed = TushareDataFeed(
                symbol=config['symbol'],
                start_date=start_date,
                end_date=end_date,
                tushare_token=tushare_token
            )
            
            # 添加策略回测
            multi_engine.add_strategy_backtest(
                strategy_name=config['strategy_name'],
                strategy_class=config['strategy_class'],
                data_feed=data_feed,
                **config['strategy_params']
            )
        
        # 4. 运行所有回测
        results = multi_engine.run_all_backtests()
        
        # 5. 生成综合报告
        report = multi_engine.generate_comprehensive_report()
        print(report)
        
        # 6. 绘制所有结果
        multi_engine.plot_all_results('multi_strategy_plots')
        
        # 7. 保存所有结果
        multi_engine.save_all_results('multi_strategy_results.json')
        
        # 8. 详细分析
        analyzer = BacktestResultsAnalyzer(results)
        
        # 生成详细报告
        detailed_report = analyzer.generate_detailed_report()
        print(detailed_report)
        
        # 绘制分析图表
        analyzer.plot_performance_comparison('performance_comparison.png')
        analyzer.plot_risk_return_scatter('risk_return_scatter.png')
        analyzer.plot_trading_metrics('trading_metrics.png')
        
        # 导出到Excel
        analyzer.export_to_excel('detailed_analysis.xlsx')
        
        logger.info("多策略回测完成")
        
    except Exception as e:
        logger.error(f"多策略回测失败: {e}")


def run_parameter_optimization():
    """运行参数优化示例"""
    logger.info("开始参数优化示例")
    
    # 配置参数
    symbol = '000001.SZ'
    start_date = '20230101'
    end_date = '20231231'
    tushare_token = 'your_tushare_token'
    
    # 参数组合
    param_combinations = [
        {'short_window': 5, 'long_window': 10},
        {'short_window': 5, 'long_window': 20},
        {'short_window': 10, 'long_window': 20},
        {'short_window': 10, 'long_window': 30},
        {'short_window': 20, 'long_window': 30},
    ]
    
    results = {}
    
    try:
        for i, params in enumerate(param_combinations):
            logger.info(f"测试参数组合 {i+1}: {params}")
            
            # 创建数据源
            data_feed = TushareDataFeed(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                tushare_token=tushare_token
            )
            
            # 创建回测引擎
            engine = BacktraderEngine(
                initial_cash=1000000,
                commission=0.001
            )
            
            # 添加数据源和策略
            engine.add_data(data_feed, name=symbol)
            engine.add_strategy(MAStrategy, strategy_name=f'MA_Strategy_{i}', **params)
            
            # 运行回测
            result = engine.run_backtest(f'MA_Strategy_{i}')
            
            if result:
                results[f'MA_Strategy_{i}'] = result
                logger.info(f"参数组合 {i+1} 完成: 收益率 {result.total_return:.2%}")
        
        # 分析优化结果
        if results:
            analyzer = BacktestResultsAnalyzer(results)
            
            # 找到最佳参数
            best_strategy = analyzer.get_best_strategy('total_return')
            print(f"最佳策略: {best_strategy}")
            
            # 生成优化报告
            optimization_report = analyzer.generate_detailed_report()
            print(optimization_report)
            
            # 保存优化结果
            analyzer.export_to_excel('parameter_optimization_results.xlsx')
        
        logger.info("参数优化完成")
        
    except Exception as e:
        logger.error(f"参数优化失败: {e}")


def run_csv_data_backtest():
    """使用CSV数据运行回测示例"""
    logger.info("开始CSV数据回测示例")
    
    try:
        # 创建CSV数据源（假设有CSV文件）
        csv_feed = CSVDataFeed('data/stock_data.csv')
        
        # 创建回测引擎
        engine = BacktraderEngine(
            initial_cash=1000000,
            commission=0.001
        )
        
        # 添加数据源和策略
        engine.add_data(csv_feed, name='CSV_Data')
        engine.add_strategy(BollingerBandsStrategy, strategy_name='BB_Strategy')
        
        # 运行回测
        result = engine.run_backtest('BB_Strategy')
        
        if result:
            print(f"CSV回测完成: 收益率 {result.total_return:.2%}")
        
        logger.info("CSV数据回测完成")
        
    except Exception as e:
        logger.error(f"CSV数据回测失败: {e}")


def main():
    """主函数"""
    logger.info("开始 Backtrader 回测框架示例")
    
    # 运行各种示例
    try:
        # 1. 单策略回测
        run_single_strategy_backtest()
        
        # 2. 多策略回测
        run_multi_strategy_backtest()
        
        # 3. 参数优化
        run_parameter_optimization()
        
        # 4. CSV数据回测
        run_csv_data_backtest()
        
        logger.info("所有示例运行完成")
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}")


if __name__ == "__main__":
    main() 