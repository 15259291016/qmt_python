from datetime import datetime, timedelta

def get_utc8_datetime() -> datetime:
    return datetime.utcnow() + timedelta(hours=8)
