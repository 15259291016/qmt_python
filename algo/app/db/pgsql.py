import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, DateTime, Float, \
    UniqueConstraint, Numeric
from sqlalchemy.exc import IntegrityError
# 使用SQLAlchemy的DeclarativeBase来定义模型
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base

Base = declarative_base()
metadata = MetaData()
load_dotenv()
DATABASE_URL = os.getenv('PGSQL_ENGINE_URL')

#

class ChatGroup(Base):
    __tablename__ = 'chat_groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Stock(Base):
    __tablename__ = 'stocks'
    name = Column(String, primary_key=True)


class ShareRecord(Base):
    __tablename__ = 'share_records'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('chat_groups.id'), nullable=False)
    stock_name = Column(String, ForeignKey('stocks.name'), nullable=False)
    share_time = Column(DateTime, default=datetime.utcnow)

    chat_group = relationship("ChatGroup")
    stock = relationship("Stock")

# 定义数据模型
class RecordOfTotalTurnover(Base):
    __tablename__ = 'recordoftotalturnover'
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_time = Column(DateTime, unique=True, default=datetime.utcnow)
    current_amount = Column(Numeric(15, 2), nullable=False)
    northbound_inflow = Column(Numeric(15, 2), nullable=False)
    northbound_outflow = Column(Numeric(15, 2), nullable=False)
    all = Column(Numeric(15, 2), nullable=False)

    __table_args__ = (UniqueConstraint('transaction_time', name='uq_transaction_time'),)

class tjItem(Base):
    __tablename__ = 'tjitem'
    id = Column(Integer, primary_key=True)
    qm = Column(String)
    info = Column(String)

class WatchCode(Base):
    __tablename__ = 'watchcode'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    market = Column(String)
    create_time = Column(DateTime, default=datetime.utcnow)

class WaitBuyList(Base):
    __tablename__ = 'waitbuylist'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    market = Column(String)
    create_time = Column(DateTime, default=datetime.utcnow)


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()


def get_items(skip: int = 0, limit: int = 100):
    return db.query(tjItem).offset(skip).limit(limit).all()


def create(obj):
    try:
        db.add(obj)
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        print(e)
    return obj

def update(obj):
    return db.query(obj).all()


def read(obj):
    return db.query(obj).all()


def get_db():
    return db

# 示例：插入数据
def add_record(current_amount: float, northbound_inflow: float, northbound_outflow: float,all: float):
    db = get_db()
    new_record = RecordOfTotalTurnover(
        transaction_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        current_amount=current_amount,
        northbound_inflow=northbound_inflow,
        northbound_outflow=northbound_outflow,
        all=all
    )
    try:
        db.add(new_record)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Transaction time must be unique")
    finally:
        db.close()

# 示例：查询数据
def get_records():
    db = get_db()
    records = db.query(RecordOfTotalTurnover).all()
    db.close()
    return records


if __name__ == '__main__':
    Base.metadata.create_all(engine)
