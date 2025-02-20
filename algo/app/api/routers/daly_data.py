from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.db import pgsql

router = APIRouter()

class RecordOfTotalTurnover(BaseModel):
    id: Optional[int] = None
    transaction_time: datetime = None
    current_amount: float
    northbound_inflow: float
    northbound_outflow: float

    class Config:
        from_attributes = True

@router.post("/records", tags=["新增交易信息数据"], response_model=RecordOfTotalTurnover)
async def create_record(record: RecordOfTotalTurnover):
    insert_data_query = """
            INSERT INTO RecordOfTotalTurnover (current_amount, northbound_inflow, northbound_outflow)
            VALUES (%s, %s, %s)
            ON CONFLICT (transaction_time) DO NOTHING;;
            """
    db = pgsql.get_db()
    db.execute(insert_data_query, (record.transaction_time, record.current_amount, record.northbound_inflow, record.northbound_outflow))
    record_id = db.fetchone()[0]
    db.commit()
    db.close()

    record.id = record_id
    return record



