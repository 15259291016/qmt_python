from tornado.web import RequestHandler, Application
from modules.tornadoapp.risk.risk_manager import RiskManager
import json

risk_manager = RiskManager()

class RiskConfigHandler(RequestHandler):
    def get(self):
        self.write({
            "max_single_order_amount": risk_manager.max_single_order_amount,
            "max_daily_amount": risk_manager.max_daily_amount,
            "blacklist": list(risk_manager.blacklist)
        })
    def post(self):
        data = json.loads(self.request.body.decode())
        if "max_single_order_amount" in data:
            risk_manager.max_single_order_amount = data["max_single_order_amount"]
        if "max_daily_amount" in data:
            risk_manager.max_daily_amount = data["max_daily_amount"]
        self.write({"msg": "风控参数已更新"})

class BlacklistHandler(RequestHandler):
    def get(self):
        self.write({"blacklist": list(risk_manager.blacklist)})
    def post(self):
        data = json.loads(self.request.body.decode())
        symbol = data.get("symbol")
        if symbol:
            risk_manager.add_to_blacklist(symbol)
            self.write({"msg": f"{symbol} 已加入黑名单"})
        else:
            self.set_status(400)
            self.write({"msg": "缺少symbol参数"})
    def delete(self):
        data = json.loads(self.request.body.decode())
        symbol = data.get("symbol")
        if symbol:
            risk_manager.remove_from_blacklist(symbol)
            self.write({"msg": f"{symbol} 已移除黑名单"})
        else:
            self.set_status(400)
            self.write({"msg": "缺少symbol参数"}) 