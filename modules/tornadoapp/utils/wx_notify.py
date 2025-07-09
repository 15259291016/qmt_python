import os
import httpx
from modules.tornadoapp.model.wx_bind import WxBind

# 从环境变量读取微信公众号推送相关配置
WECHAT_APPID = os.getenv("WECHAT_APPID")
WECHAT_SECRET = os.getenv("WECHAT_SECRET")
WECHAT_TEMPLATE_ID = os.getenv("WECHAT_TEMPLATE_ID")
WECHAT_ADMIN_OPENIDS = os.getenv("WECHAT_ADMIN_OPENIDS", "")  # 支持逗号分隔多个openId

async def get_access_token():
    """
    获取微信公众号全局access_token
    """
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APPID}&secret={WECHAT_SECRET}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
        return data.get("access_token")

async def send_wx_register_notify(username, email):
    """
    用户注册成功后，向所有配置的管理员openId推送通知
    优先使用环境变量WECHAT_ADMIN_OPENIDS，无则查WxBind表
    """
    # 优先从环境变量获取openId
    openids = [oid.strip() for oid in WECHAT_ADMIN_OPENIDS.split(",") if oid.strip()]
    if not openids:
        # 数据库查找
        binds = await WxBind.find({"is_active": True, "bind_type": "admin"}).to_list()
        openids = [b.openid for b in binds]
    if not openids:
        return

    access_token = await get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

    for openid in openids:
        payload = {
            "touser": openid,
            "template_id": WECHAT_TEMPLATE_ID,
            "data": {
                "first": {"value": "有新用户注册成功！"},
                "keyword1": {"value": username},
                "keyword2": {"value": email},
                "remark": {"value": "请及时关注新用户动态。"}
            }
        }
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload) 