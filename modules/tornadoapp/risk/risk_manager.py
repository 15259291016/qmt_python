class RiskManager:
    def __init__(self):
        self.max_single_order_amount = 1000000  # 单笔最大金额
        self.max_daily_amount = 10000000        # 日内最大金额
        self.blacklist = set()                  # 股票黑名单
        self.daily_amount = 0                   # 当日累计交易金额

    def check_order(self, symbol, price, quantity, account):
        if symbol in self.blacklist:
            return False, f"股票{symbol}在黑名单中，禁止交易"
        order_amount = price * quantity
        if order_amount > self.max_single_order_amount:
            return False, f"单笔下单金额超限: {order_amount} > {self.max_single_order_amount}"
        if self.daily_amount + order_amount > self.max_daily_amount:
            return False, f"日内累计下单金额超限: {self.daily_amount + order_amount} > {self.max_daily_amount}"
        return True, "风控通过"

    def on_order_filled(self, price, quantity):
        self.daily_amount += price * quantity

    def add_to_blacklist(self, symbol):
        self.blacklist.add(symbol)

    def remove_from_blacklist(self, symbol):
        self.blacklist.discard(symbol) 