from beanie import Document
from pydantic import Field

class WxBind(Document):
    user_id: str = Field(..., description="系统用户ID")
    openid: str = Field(..., description="微信openId")
    bind_type: str = Field(default="admin", description="绑定类型")
    is_active: bool = Field(default=True)
    
    class Settings:
        name = "wx_binds" 