import pandas as pd
import numpy as np
import random

class BacktestEngine:
    def __init__(self, strategies, data, accounts, initial_capital=1000000, slippage=0.01, fill_prob=1.0):
        """
        strategies: dict, {account_id: strategy_obj}
        data: DataFrame, 必须包含['datetime','symbol','open','high','low','close','volume']
        accounts: list, 账户ID列表
        initial_capital: 初始资金
        slippage: 滑点（元）
        fill_prob: 成交概率（0-1）
        """
        self.strategies = strategies
        self.data = data
        self.accounts = {aid: {'cash': initial_capital, 'positions': {}} for aid in accounts}
        self.orders = []
        self.trades = []
        self.equity_curve = {aid: [] for aid in accounts}
        self.slippage = slippage
        self.fill_prob = fill_prob

    def run(self):
        for idx, bar in self.data.iterrows():
            symbol = bar['symbol']
            for aid, strategy in self.strategies.items():
                # 策略信号
                signal = strategy.on_bar(bar, aid)
                account = self.accounts[aid]
                # 买入
                if signal == 1:
                    price = bar['close'] + self.slippage
                    if random.random() < self.fill_prob:
                        if account['cash'] >= price * 100:
                            account['positions'][symbol] = account['positions'].get(symbol, 0) + 100
                            account['cash'] -= price * 100
                            self.orders.append({'account': aid, 'type': 'buy', 'symbol': symbol, 'price': price, 'volume': 100, 'datetime': bar['datetime']})
                # 卖出
                elif signal == -1:
                    price = bar['close'] - self.slippage
                    if random.random() < self.fill_prob:
                        if account['positions'].get(symbol, 0) >= 100:
                            account['positions'][symbol] -= 100
                            account['cash'] += price * 100
                            self.orders.append({'account': aid, 'type': 'sell', 'symbol': symbol, 'price': price, 'volume': 100, 'datetime': bar['datetime']})
                # 记录每日权益
                pos_value = sum([bar['close'] * v for s, v in account['positions'].items() if s == symbol])
                equity = account['cash'] + pos_value
                self.equity_curve[aid].append({'datetime': bar['datetime'], 'equity': equity})
        return self.generate_report()

    def generate_report(self):
        reports = {}
        for aid, curve in self.equity_curve.items():
            df = pd.DataFrame(curve)
            df['return'] = df['equity'].pct_change().fillna(0)
            total_return = df['equity'].iloc[-1] / df['equity'].iloc[0] - 1
            annual_return = (1 + total_return) ** (252 / len(df)) - 1
            sharpe = df['return'].mean() / df['return'].std() * (252 ** 0.5) if df['return'].std() > 0 else 0
            max_drawdown = ((df['equity'].cummax() - df['equity']) / df['equity'].cummax()).max()
            reports[aid] = {
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe': sharpe,
                'max_drawdown': max_drawdown,
                'orders': [o for o in self.orders if o['account'] == aid],
                'equity_curve': df
            }
        return reports 