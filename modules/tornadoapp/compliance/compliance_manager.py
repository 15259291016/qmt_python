class ComplianceManager:
    def __init__(self):
        self.rules = []  # 合规规则列表
        self.logs = []   # 合规日志

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def check(self, order):
        for rule in self.rules:
            if not rule(order):
                self.logs.append((order, "合规校验失败"))
                return False
        self.logs.append((order, "合规校验通过"))
        return True

    def get_logs(self):
        return self.logs 