from datetime import datetime

from beanie import Document
from pydantic import Field


class DemoModel(Document):
    name: str
    age: int
    email: str
    phone: str
    address: str
    create_time: datetime
    update_time: datetime
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)

    class Config:
        collection = "demo"

    def to_dict(self):
        return {
            "name": self.name,
            "age": self.age
        }
        