# coding=utf-8
"""
Backtrader 框架测试脚本
验证新框架的基本功能
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_mock_data():
    """创建模拟数据用于测试"""
    logger.info("创建模拟数据")
    
    # 生成模拟股票数据
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    
    # 模拟价格数据
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.001, 0.02, len(dates))  # 每日收益率
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # 创建OHLCV数据
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # 模拟OHLC数据
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = prices[i-1] if i > 0 else price
        volume = np.random.randint(1000000, 10000000)
        
        data.append({
            'datetime': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    logger.info(f"模拟数据创建完成: {len(df)} 条记录")
    return df


def test_backtrader_import():
    """测试 Backtrader 导入"""
    try:
        import backtrader as bt
        logger.info("✓ Backtrader 导入成功")
        return True
    except ImportError as e:
        logger.error(f"✗ Backtrader 导入失败: {e}")
        return False


def test_strategy_base():
    """测试策略基类"""
    try:
        from modules.backtrader_engine.strategy_base import BacktraderStrategyBase, MAStrategy
        
        logger.info("✓ 策略基类导入成功")
        
        # 测试策略参数
        strategy = MAStrategy(short_window=5, long_window=20)
        params = strategy.get_params()
        logger.info(f"✓ 策略参数获取成功: {params}")
        
        return True
    except Exception as e:
        logger.error(f"✗ 策略基类测试失败: {e}")
        return False


def test_data_feed():
    """测试数据源适配器"""
    try:
        from modules.backtrader_engine.data_feed import CSVDataFeed
        
        # 创建模拟数据
        mock_df = create_mock_data()
        
        # 保存为CSV文件
        csv_file = 'test_data.csv'
        mock_df.to_csv(csv_file)
        
        # 测试CSV数据源
        feed = CSVDataFeed(csv_file)
        logger.info("✓ CSV数据源创建成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 数据源测试失败: {e}")
        return False


def test_backtest_engine():
    """测试回测引擎"""
    try:
        from modules.backtrader_engine.backtest_engine import BacktraderEngine
        from modules.backtrader_engine.strategy_base import MAStrategy
        
        # 创建模拟数据
        mock_df = create_mock_data()
        
        # 保存为CSV文件
        csv_file = 'test_data.csv'
        mock_df.to_csv(csv_file)
        
        # 创建回测引擎
        engine = BacktraderEngine(
            initial_cash=1000000,
            commission=0.001
        )
        
        # 添加数据源
        from modules.backtrader_engine.data_feed import CSVDataFeed
        data_feed = CSVDataFeed(csv_file)
        engine.add_data(data_feed, name='test_data')
        
        # 添加策略
        engine.add_strategy(MAStrategy, strategy_name='test_strategy')
        
        logger.info("✓ 回测引擎创建成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 回测引擎测试失败: {e}")
        return False


def test_results_analyzer():
    """测试结果分析器"""
    try:
        from modules.backtrader_engine.results_analyzer import BacktestResultsAnalyzer
        from modules.backtrader_engine.backtest_engine import BacktestResult
        
        # 创建模拟结果
        mock_results = {
            'strategy1': BacktestResult(
                strategy_name='strategy1',
                symbol='000001.SZ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_cash=1000000,
                final_value=1100000,
                total_return=0.1,
                annual_return=0.1,
                sharpe_ratio=1.2,
                max_drawdown=0.05,
                win_rate=0.6,
                total_trades=10,
                profit_trades=6,
                loss_trades=4,
                avg_profit=1000,
                avg_loss=-500,
                profit_factor=1.5,
                equity_curve=[],
                trade_history=[]
            ),
            'strategy2': BacktestResult(
                strategy_name='strategy2',
                symbol='000002.SZ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_cash=1000000,
                final_value=1200000,
                total_return=0.2,
                annual_return=0.2,
                sharpe_ratio=1.5,
                max_drawdown=0.08,
                win_rate=0.7,
                total_trades=15,
                profit_trades=10,
                loss_trades=5,
                avg_profit=1200,
                avg_loss=-400,
                profit_factor=2.0,
                equity_curve=[],
                trade_history=[]
            )
        }
        
        # 创建分析器
        analyzer = BacktestResultsAnalyzer(mock_results)
        
        # 测试分析功能
        performance_summary = analyzer.get_performance_summary()
        best_strategy = analyzer.get_best_strategy('total_return')
        
        logger.info(f"✓ 结果分析器测试成功")
        logger.info(f"  性能摘要: {len(performance_summary)} 个策略")
        logger.info(f"  最佳策略: {best_strategy}")
        
        return True
    except Exception as e:
        logger.error(f"✗ 结果分析器测试失败: {e}")
        return False


def run_simple_backtest():
    """运行简单回测测试"""
    try:
        from modules.backtrader_engine.backtest_engine import BacktraderEngine
        from modules.backtrader_engine.strategy_base import MAStrategy
        from modules.backtrader_engine.data_feed import CSVDataFeed
        
        logger.info("开始简单回测测试")
        
        # 创建模拟数据
        mock_df = create_mock_data()
        csv_file = 'test_data.csv'
        mock_df.to_csv(csv_file)
        
        # 创建回测引擎
        engine = BacktraderEngine(
            initial_cash=1000000,
            commission=0.001
        )
        
        # 添加数据源
        data_feed = CSVDataFeed(csv_file)
        engine.add_data(data_feed, name='test_data')
        
        # 添加策略
        engine.add_strategy(MAStrategy, strategy_name='test_strategy')
        
        # 运行回测
        result = engine.run_backtest('test_strategy')
        
        if result:
            logger.info(f"✓ 回测运行成功")
            logger.info(f"  总收益率: {result.total_return:.2%}")
            logger.info(f"  夏普比率: {result.sharpe_ratio:.2f}")
            logger.info(f"  最大回撤: {result.max_drawdown:.2%}")
            logger.info(f"  胜率: {result.win_rate:.2%}")
        else:
            logger.warning("⚠ 回测未产生结果")
        
        return True
    except Exception as e:
        logger.error(f"✗ 简单回测测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("开始 Backtrader 框架测试")
    
    tests = [
        ("Backtrader 导入测试", test_backtrader_import),
        ("策略基类测试", test_strategy_base),
        ("数据源测试", test_data_feed),
        ("回测引擎测试", test_backtest_engine),
        ("结果分析器测试", test_results_analyzer),
        ("简单回测测试", run_simple_backtest),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} 通过")
            else:
                logger.error(f"✗ {test_name} 失败")
        except Exception as e:
            logger.error(f"✗ {test_name} 异常: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"测试总结: {passed}/{total} 通过")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 所有测试通过！Backtrader 框架工作正常")
    else:
        logger.warning(f"⚠ {total - passed} 个测试失败，请检查配置")


if __name__ == "__main__":
    main() 