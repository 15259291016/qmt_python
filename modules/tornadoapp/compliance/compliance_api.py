from tornado.web import RequestHandler
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
import json
import pandas as pd

compliance_manager = ComplianceManager()

class ComplianceLogHandler(RequestHandler):
    def get(self):
        logs = compliance_manager.get_logs()
        self.write({"total": len(logs), "logs": logs})

class ComplianceExportHandler(RequestHandler):
    def get(self):
        logs = compliance_manager.get_logs()
        df = pd.DataFrame(logs)
        df.to_csv("compliance_report.csv", index=False)
        self.write({"msg": "导出成功", "file": "compliance_report.csv"})

class ComplianceRuleHandler(RequestHandler):
    def get(self):
        self.write({"rules": [str(rule) for rule in compliance_manager.rules]})
    def post(self):
        # 动态添加合规规则（示例：只允许买入）
        data = json.loads(self.request.body.decode())
        rule_type = data.get("type")
        if rule_type == "only_buy":
            def only_buy_rule(order):
                return order.get("side") == "买"
            compliance_manager.add_rule(only_buy_rule)
            self.write({"msg": "已添加只允许买入规则"})
        else:
            self.set_status(400)
            self.write({"msg": "未知规则类型"}) 