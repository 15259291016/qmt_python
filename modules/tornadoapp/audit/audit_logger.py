import datetime

class AuditLogger:
    def __init__(self):
        self.records = []

    def log(self, user, action, detail):
        record = {
            'timestamp': datetime.datetime.now().isoformat(),
            'user': user,
            'action': action,
            'detail': detail
        }
        self.records.append(record)

    def query(self, user=None, action=None):
        result = self.records
        if user:
            result = [r for r in result if r['user'] == user]
        if action:
            result = [r for r in result if r['action'] == action]
        return result

    def export(self, filepath):
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2) 