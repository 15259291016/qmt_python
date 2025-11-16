import sys
from strategies.registry import get_registry
from modules.backtrader_engine.backtest_engine import BacktraderEngine
from modules.backtrader_engine.data_feed import TushareDataFeed

# 1. 获取所有Backtrader风格策略
registry = get_registry()
all_strategies = registry.list_bt_strategies()
if not all_strategies:
    print("未发现可用的Backtrader策略，请先在strategies/目录下实现并注册！")
    sys.exit(1)

print("可用策略：")
for idx, name in enumerate(all_strategies):
    print(f"{idx+1}. {name}")

# 2. 让用户选择
try:
    choice = int(input("请输入要回测的策略编号：")) - 1
    if choice < 0 or choice >= len(all_strategies):
        print("输入编号无效！")
        sys.exit(1)
except Exception:
    print("输入无效，请输入数字编号！")
    sys.exit(1)

strategy_name = all_strategies[choice]
strategy_class = registry.get_strategy(strategy_name)

# 3. 配置数据源（以Tushare为例）
tushare_token = input("请输入你的Tushare Token：").strip()
symbol = input("请输入股票代码（如002594.SZ）：").strip() or '002594.SZ'
start_date = input("请输入回测开始日期（如20220101）：").strip() or '20220101'
end_date = input("请输入回测结束日期（如20231231）：").strip() or '20231231'

print(f"正在下载 {symbol} 的历史数据...")
data_feed = TushareDataFeed.from_tushare(
    symbol=symbol,
    start_date=start_date,
    end_date=end_date,
    tushare_token=tushare_token
)

# 4. 创建回测引擎并添加策略
engine = BacktraderEngine(initial_cash=1000000)
engine.add_data(data_feed)
engine.add_strategy(strategy_class)

# 5. 运行回测
print(f"正在回测策略 {strategy_name} ...")
result = engine.run_backtest()
print("回测结果：")
print(result)

try:
    engine.plot()
except Exception as e:
    print(f"绘图失败: {e}")
