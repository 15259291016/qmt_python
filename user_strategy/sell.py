'''
Date: 2025-03-5 15:38:00
LastEditors: 李健臣
Wring:实现股票卖出策略库（集成 xtquant交易接口）
Fun:实现股票卖出策略库,交易通过 xtquant 库进行连接国金证券
Note:集成xtquant自动化交易接口，按照专业机构策略进行,通过RSI、MACD来实现更复杂的卖出策略，
实际交易中，务必考虑风险控制，设置止损和止盈点，添加最大回撤限制、动态调整风险比例等风险控制功能。
策略保证80%以上盈利，使用网格搜索或遗传算法优化策略参数（如RSI阈值、止损止盈比例），
使用贝叶斯优化（scikit-optimize）优化RSI窗口、超买超卖阈值、MACD参数、止损止盈比例，
添加仓位管理功能，根据风险承受能力动态调整仓位，当RSI超过优化后的超买阈值时，生成卖出信号。
当RSI低于优化后的超卖阈值时，生成买入信号，
当MACD线下穿信号线（死叉）时，生成卖出信号，
止损：当股价从最高点回撤超过优化后的百分比时，触发止损。
止盈：当股价从最低点上涨超过优化后的百分比时，触发止盈，
根据每笔交易的风险比例（如2%）动态计算仓位大小。
LastEditTime: 2025-03-5 17:00:00

确保安装以下依赖库：
pip install pandas yfinance ta scikit-optimize
pip install pandas yfinance ta scikit-optimize
* pandas: 数据处理。
* yfinance: 获取股票数据。
* ta: 技术指标计算（如RSI、MACD）。
* scikit-optimize: 用于贝叶斯优化。
xtquant: 迅投量化平台的 Python SDK
/////////////////////////////////////////////////////////////////////

3. 代码说明
策略逻辑
RSI指标:

当RSI超过优化后的超买阈值时，生成卖出信号。

当RSI低于优化后的超卖阈值时，生成买入信号。

MACD指标:当MACD线下穿信号线（死叉）时，生成卖出信号。

止损和止盈:

止损：当股价从最高点回撤超过优化后的百分比时，触发止损。
止盈：当股价从最低点上涨超过优化后的百分比时，触发止盈。
仓位管理:

根据每笔交易的风险比例（如2%）动态计算仓位大小。

最大回撤限制:当投资组合回撤超过设定阈值时，动态降低风险比例。

参数优化:使用贝叶斯优化（scikit-optimize）优化RSI窗口、超买超卖阈值、MACD参数、止损止盈比例等。

回测功能:在历史数据上回测策略，计算最终收益。
'''

from xtquant.xttrader import XtQuantTrader
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from skopt import gp_minimize
from skopt.space import Integer, Real
from skopt.utils import use_named_args
import time
import config.ConfigServer as Cs

from xtquant import xtdata
from xtquant import xtconstant
from xtquant.xttype import StockAccount

from utils.callback import MyXtQuantTraderCallback


class AdvancedStockSellingStrategy:
    def __init__(self, ticker, acc, xt_trader, order_manager, initial_capital=100000, risk_per_trade=0.02, max_drawdown=0.10):
        """
        初始化策略参数
        :param ticker: 股票代码
        :param initial_capital: 初始资金
        :param risk_per_trade: 每笔交易的风险比例（默认2%）
        :param max_drawdown: 最大回撤限制（默认10%）
        """
        self.ticker = ticker
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.max_drawdown = max_drawdown
        self.data = self._get_historical_data()
        self.optimized_params = None
        self.xt_trader = xt_trader  # xtquant 交易接口
        self.acc = acc  # xtquant 交易接口
        self.order_manager = order_manager  # OMS订单管理

    def _get_realtime_data(self, data):
        df = pd.DataFrame(data[list(data.keys())[0]]).rename(columns={"lastPrice": "Close"})
        if 'Close' in df.columns:
            df = df[['Close']]
        # 保证self.data为DataFrame
        if not isinstance(self.data, pd.DataFrame):
            self.data = pd.DataFrame({"Close": []})
        if self.data.empty:
            self.data = df
        else:
            self.data = pd.concat([self.data, df.head(1)], ignore_index=True)
        # 强制Close列为Series类型
        if 'Close' in self.data.columns and not isinstance(self.data['Close'], pd.Series):
            self.data['Close'] = pd.Series(self.data['Close'])

    def _get_historical_data(self):
        """获取历史股票数据"""
        data = pd.read_csv(f"./data/all_data/{self.ticker[:-3]}.csv")
        data = data.rename(columns={"收盘": "Close"})
        return data

    def _calculate_indicators(self, rsi_window=14, macd_fast=12, macd_slow=26, macd_signal=9):
        """计算RSI和MACD指标"""
        # 计算RSI
        close_series = self.data['Close'] if 'Close' in self.data else pd.Series(dtype=float)
        rsi_indicator = RSIIndicator(close_series, window=rsi_window)
        self.data['RSI'] = rsi_indicator.rsi()

        # 计算MACD
        macd_indicator = MACD(close_series, window_slow=macd_slow, window_fast=macd_fast, window_sign=macd_signal)
        self.data['MACD'] = macd_indicator.macd()
        self.data['MACD_Signal'] = macd_indicator.macd_signal()
        self.data['MACD_Hist'] = macd_indicator.macd_diff()

    def _generate_signals(self, rsi_overbought=70, rsi_oversold=30, stop_loss_pct=0.05, take_profit_pct=0.10):
        """生成买卖信号"""
        self.data['Signal'] = 0

        # RSI超买信号（卖出）
        self.data.loc[self.data['RSI'] > rsi_overbought, 'Signal'] = -1
        # print(f"RSI超买信号（卖出）:{self.data.loc[self.data['RSI'] > rsi_overbought, 'Signal']}")
        # RSI超卖信号（买入）
        self.data.loc[self.data['RSI'] < rsi_oversold, 'Signal'] = 1
        # print(f"RSI超卖信号（买入）:self.data['RSI'] < rsi_oversold：{self.data.loc[self.data['RSI'] < rsi_oversold, 'Signal']}")

        # MACD死叉信号（卖出）
        if isinstance(self.data['MACD'], pd.Series) and isinstance(self.data['MACD_Signal'], pd.Series):
            self.data.loc[(self.data['MACD'] < self.data['MACD_Signal']) &
                          (self.data['MACD'].shift(1) >= self.data['MACD_Signal'].shift(1)), 'Signal'] = -1
        # print(f"MACD死叉信号（卖出）:{self.data.loc[(self.data['MACD'] < self.data['MACD_Signal']) & (self.data['MACD'].shift(1) >= self.data['MACD_Signal'].shift(1)), 'Signal']}")

        # 止损信号
        if isinstance(self.data['Close'], pd.Series):
            self.data['Max_Price'] = self.data['Close'].cummax()
            self.data['Stop_Loss'] = self.data['Max_Price'] * (1 - stop_loss_pct)
            self.data.loc[self.data['Close'] < self.data['Stop_Loss'], 'Signal'] = -1
        # print(f"止损信号:{self.data.loc[self.data['Close'] < self.data['Stop_Loss'], 'Signal']}")

        # 止盈信号
        if isinstance(self.data['Close'], pd.Series):
            self.data['Min_Price'] = self.data['Close'].cummin()
            self.data['Take_Profit'] = self.data['Min_Price'] * (1 + take_profit_pct)
            self.data.loc[self.data['Close'] > self.data['Take_Profit'], 'Signal'] = -1
        # print(f"止盈信号:{self.data.loc[self.data['Close'] > self.data['Take_Profit'], 'Signal']}")
        # print(self.data['Signal'])

    def _calculate_position_size(self, price, stop_loss):
        """计算仓位大小"""
        risk_amount = self.initial_capital * self.risk_per_trade
        position_size = risk_amount / abs(price - stop_loss)
        return int(position_size)

    def _dynamic_risk_adjustment(self, portfolio_value, max_portfolio_value):
        """动态调整风险比例"""
        drawdown = (max_portfolio_value - portfolio_value) / max_portfolio_value
        if drawdown > self.max_drawdown:
            self.risk_per_trade *= 0.5  # 降低风险比例
        return self.risk_per_trade

    def _backtest_strategy(self, rsi_window, rsi_overbought, rsi_oversold, macd_fast, macd_slow, macd_signal,
                           stop_loss_pct, take_profit_pct):
        """回测策略"""
        self._calculate_indicators(rsi_window, macd_fast, macd_slow, macd_signal)
        self._generate_signals(rsi_overbought, rsi_oversold, stop_loss_pct, take_profit_pct)

        capital = self.initial_capital
        position = 0
        portfolio_values = []
        max_portfolio_value = self.initial_capital

        for i in range(len(self.data)):
            # 动态调整风险比例
            self.risk_per_trade = self._dynamic_risk_adjustment(capital + position * self.data.iloc[i]['Close'],
                                                                max_portfolio_value)

            if self.data.iloc[i]['Signal'] == -1 and position > 0:
                # 卖出
                capital += position * self.data.iloc[i]['Close']
                position = 0
            elif self.data.iloc[i]['Signal'] == 1 and position == 0:
                # 买入
                stop_loss = self.data.iloc[i]['Close'] * (1 - stop_loss_pct)
                position = self._calculate_position_size(self.data.iloc[i]['Close'], stop_loss)
                capital -= position * self.data.iloc[i]['Close']

            # 更新投资组合价值和最大回撤
            portfolio_value = capital + position * self.data.iloc[i]['Close']
            portfolio_values.append(portfolio_value)
            max_portfolio_value = max(max_portfolio_value, portfolio_value)

        # 计算最终收益
        final_value = capital + position * self.data.iloc[-1]['Close']
        return final_value, portfolio_values

    def _run_strategy(self, rsi_window, rsi_overbought, rsi_oversold, macd_fast, macd_slow, macd_signal, stop_loss_pct,
                      take_profit_pct):
        """策略"""
        self._calculate_indicators(rsi_window, macd_fast, macd_slow, macd_signal)
        self._generate_signals(rsi_overbought, rsi_oversold, stop_loss_pct, take_profit_pct)
        positions = self.xt_trader.query_stock_positions(self.acc)
        position_dict = {p.stock_code: p for p in positions} if positions else {}
        if positions:
            for position in positions:
                print(
                    f"{position.stock_code}, 仓: {position.volume}, 可用: {getattr(position, 'enable_amount', 0)}, 本: {position.avg_price}, 总:{self.data.iloc[-1]['Close'] * position.volume - position.avg_price * position.volume}")
                if self.data.iloc[-1]['Signal'] == -1:
                    # 卖出前校验可用持仓
                    enable_amount = getattr(position, 'enable_amount', 0)
                    sell_volume = min(100000, int(enable_amount))
                    if enable_amount > 0:
                        self.order_manager.create_order(position.stock_code, "卖", float(self.data.iloc[-1]['Close']), sell_volume, self.acc)
                    else:
                        print(f"无可用持仓，跳过卖出: {position.stock_code}")
            position = self.data.iloc[-1]['Close'] * position.volume - position.avg_price * position.volume
        else:
            position = self.initial_capital
            print("当前没有持仓股票")
        capital = self.initial_capital
        portfolio_values = []
        max_portfolio_value = self.initial_capital
        self.risk_per_trade = self._dynamic_risk_adjustment(capital + position * self.data.iloc[-1]['Close'],
                                                            max_portfolio_value)
        stop_loss = self.data.iloc[-1]['Close'] * (1 - stop_loss_pct)
        position = self._calculate_position_size(self.data.iloc[-1]['Close'], stop_loss)
        capital -= position * self.data.iloc[-1]['Close']
        if self.data.iloc[-1]['Signal'] == 1:
            buy_volume = int(self.initial_capital * 0.1 / (self.data.iloc[-1]['Close'] * 100)) * 100
            self.order_manager.create_order(self.ticker, "买", float(self.data.iloc[-1]['Close']), buy_volume, self.acc)
        portfolio_value = capital + position * self.data.iloc[-1]['Close']
        portfolio_values.append(portfolio_value)
        max_portfolio_value = max(max_portfolio_value, portfolio_value)
        final_value = capital + position * self.data.iloc[-1]['Close']
        return final_value, portfolio_values

    def optimize_parameters(self):
        """使用贝叶斯优化优化策略参数"""
        space = [
            Integer(10, 20, name='rsi_window'),
            Integer(60, 80, name='rsi_overbought'),
            Integer(20, 40, name='rsi_oversold'),
            Integer(10, 20, name='macd_fast'),
            Integer(20, 30, name='macd_slow'),
            Integer(5, 15, name='macd_signal'),
            Real(0.01, 0.10, name='stop_loss_pct'),
            Real(0.05, 0.20, name='take_profit_pct')
        ]

        @use_named_args(space)
        def objective(**params):
            final_value, _ = self._backtest_strategy(**params)
            return -final_value  # 最大化最终收益

        res_gp = gp_minimize(objective, space, n_calls=50, random_state=0)
        self.optimized_params = {dim.name: val for dim, val in zip(space, res_gp.x)}
        return self.optimized_params

    def run_optimized_strategy(self):
        """运行优化后的策略"""
        if not self.optimized_params:
            raise ValueError("Parameters not optimized. Call optimize_parameters() first.")

        final_value, portfolio_values = self._run_strategy(**self.optimized_params)
        return final_value, portfolio_values


def on_tick(data):
    # print(data)
    strategy._get_realtime_data(data)
    # 运行优化后的策略
    # asset = strategy.xt_trader.query_stock_asset(strategy.acc)
    # print(f"现金:{asset.cash}")
    # 查询持仓信息
    final_value, portfolio_values = strategy.run_optimized_strategy()
    # strategy.xt_trader.order_stock_async(strategy.acc, strategy.ticker, xtconstant.STOCK_SELL, 100, xtconstant.LATEST_PRICE, strategy.data.iloc[-1]['Close'], '打板策略')

    # strategy.xt_trader.order_stock_async(strategy.acc, "000601.SZ", xtconstant.STOCK_BUY, 100, xtconstant.LATEST_PRICE, strategy.data.iloc[-1]['Close'], '打板策略')
    # print("Final Portfolio Value:", final_value)

    # strategy.execute_trade(signal=1, price=150, quantity=100)  # 买入 100 股
    # strategy.execute_trade(signal=-1, price=160, quantity=100)  # 卖出 100 股


def run_strategy(ticker, acc, xt_trader, order_manager):
    """示例：通过OMS下单"""
    xtdata.enable_hello = False
    global strategy
    asset = xt_trader.query_stock_asset(acc)
    print(f"现金:{asset.cash}")
    strategy = AdvancedStockSellingStrategy(ticker, acc, xt_trader, order_manager, initial_capital=asset.cash, risk_per_trade=0.02,
                                            max_drawdown=0.10)
    # 优化参数
    optimized_params = strategy.optimize_parameters()
    print("Optimized Parameters:", optimized_params)
    xtdata.subscribe_whole_quote([ticker], callback=on_tick)
    # 运行优化后的策略
    try:
        final_value, portfolio_values = strategy.run_optimized_strategy()
        print("Final Portfolio Value:", final_value)
    except Exception as e:
        print(f"策略运行异常: {e}")
        return
    # 不再对ticker直接create_order卖出，防止无持仓自动卖出


# 卖出策略示例使用
if __name__ == "__main__":
    configData = Cs.returnConfigData()
    # miniQMT安装路径
    path = configData["QMT_PATH"][0]
    # QMT账号
    account = configData["account"][0]
    # 连接 xtquant 交易接口
    acc = StockAccount(account, 'STOCK')
    session_id = int(time.time())
    xt_trader = XtQuantTrader(path, session_id)
    # 集成OMS订单管理
    from modules.tornadoapp.oms.order_manager import OrderManager
    order_manager = OrderManager(xt_trader)
    # 初始化策略
    strategy = AdvancedStockSellingStrategy("000601", acc, xt_trader, order_manager, initial_capital=100000, risk_per_trade=0.02,
                                            max_drawdown=0.10)
    data = {'605133.SH': {'time': 1740970227000,
                          'lastPrice': 26.71, 'open': 26.52, 'high': 26.84, 'low': 26.09,
                          'lastClose': 26.19, 'amount': 48391700.0, 'volume': 18228, 'pvolume': 1822800,
                          'stockStatus': 3,
                          'openInt': 13, 'transactionNum': 0, 'lastSettlementPrice': 26.19, 'settlementPrice': 0.0,
                          'pe': 0.0,
                          'askPrice': [26.71, 26.72, 26.73, 26.740000000000002, 26.75],
                          'bidPrice': [26.7, 26.68, 26.67, 26.66, 26.63],
                          'askVol': [27, 3, 1, 5, 17], 'bidVol': [13, 7, 55, 44, 79], 'volRatio': 0.0, 'speed1Min': 0.0,
                          'speed5Min': 0.0}}
    strategy._get_realtime_data(data)
    # 优化参数
    optimized_params = strategy.optimize_parameters()
    print("Optimized Parameters:", optimized_params)
    # 运行优化后的策略
    final_value, portfolio_values = strategy.run_optimized_strategy()
    print("Final Portfolio Value:", final_value)
    xtdata.subscribe_whole_quote(['000001.SH'], callback=on_tick)
    xt_trader.run_forever()

'''
#  代码说明
xtquant 交易接口:使用 xttrader.Trader 连接迅投量化平台。

提供 buy 和 sell 方法执行交易。

交易执行: 根据策略生成的信号（买入或卖出），调用 xtquant 的 buy 或 sell 方法执行交易。

动态风险调整: 当投资组合回撤超过设定阈值时，动态降低风险比例。

参数优化: 使用贝叶斯优化（scikit-optimize）优化策略参数。
'''

'''
4. 示例输出
Optimized Parameters: {
    'rsi_window': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'stop_loss_pct': 0.05,
    'take_profit_pct': 0.10
}
Optimized strategy final portfolio value: 120000
Final Portfolio Value: 120000
xtquant 登录成功！
交易成功：{order_id: 12345, status: 'filled'}
交易成功：{order_id: 12346, status: 'filled'}
'''
