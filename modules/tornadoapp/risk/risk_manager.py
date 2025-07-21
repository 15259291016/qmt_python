import asyncio

class RiskManager:
    def __init__(self):
        self.rules = []
        self.logs = []

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def check_order(self, symbol, price, quantity, account):
        for rule in self.rules:
            result = rule(symbol, price, quantity, account)
            if not result:
                self.logs.append((symbol, price, quantity, account, "风控校验失败"))
                return False, "风控校验失败"
        self.logs.append((symbol, price, quantity, account, "风控校验通过"))
        return True, ""

    def on_order_filled(self, price, filled_quantity):
        # 可扩展风控逻辑
        pass

    def add_to_blacklist(self, symbol):
        self.blacklist.add(symbol)

    def remove_from_blacklist(self, symbol):
        self.blacklist.discard(symbol) 