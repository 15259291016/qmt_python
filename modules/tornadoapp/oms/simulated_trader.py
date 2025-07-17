import time

class SimulatedTrader:
    def __init__(self, data_stream, strategy, order_manager):
        self.data_stream = data_stream  # 可迭代行情数据（如生成器、列表等）
        self.strategy = strategy        # 策略对象，需实现on_tick、on_order等接口
        self.order_manager = order_manager  # 注入风控、合规、审计能力
        self.position = 0
        self.cash = 1000000
        self.orders = []

    def run(self):
        for tick in self.data_stream:
            signal = self.strategy.on_tick(tick)
            # 简单信号：1买 -1卖 0不动
            if signal == 1 and self.cash >= tick['price'] * 100:
                order = self.order_manager.create_order(tick['symbol'], "买", tick['price'], 100, "sim_account")
                if order:
                    self.position += 100
                    self.cash -= tick['price'] * 100
                    self.orders.append(order)
            elif signal == -1 and self.position >= 100:
                order = self.order_manager.create_order(tick['symbol'], "卖", tick['price'], 100, "sim_account")
                if order:
                    self.position -= 100
                    self.cash += tick['price'] * 100
                    self.orders.append(order)
            # 可插入风控、合规、审计等更多逻辑
            time.sleep(0.01)  # 仿真延迟
        print(f"仿真盘结束，最终持仓: {self.position}, 现金: {self.cash}")
        return self.orders 