from tornado.web import RequestHandler
from modules.tornadoapp.model.user_model import User
from datetime import datetime, timedelta
import json

class SubscribeHandler(RequestHandler):
    async def post(self):
        data = json.loads(self.request.body)
        user_id = data.get("user_id")
        months = int(data.get("months", 1))
        user = await User.get(user_id)
        now = datetime.utcnow()
        if user.subscription_expire_at and user.subscription_expire_at > now:
            user.subscription_expire_at += timedelta(days=30*months)
        else:
            user.subscription_expire_at = now + timedelta(days=30*months)
        await user.save()
        return {"expire_at": user.subscription_expire_at.isoformat()} 