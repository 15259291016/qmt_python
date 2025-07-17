from tornado.web import RequestHandler
from modules.tornadoapp.audit.audit_logger import AuditLogger
import json
import pandas as pd

audit_logger = AuditLogger()

class AuditLogHandler(RequestHandler):
    def get(self):
        user = self.get_argument("user", None)
        action = self.get_argument("action", None)
        logs = audit_logger.query(user=user, action=action)
        self.write({"total": len(logs), "logs": logs})

class AuditExportHandler(RequestHandler):
    def get(self):
        logs = audit_logger.records
        df = pd.DataFrame(logs)
        df.to_csv("audit_report.csv", index=False)
        self.write({"msg": "导出成功", "file": "audit_report.csv"}) 