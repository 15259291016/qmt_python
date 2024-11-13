import telebot
from get_config import get_config
import socket
import socks

import requests
# 替换为您的 Telegram Bot Token
bot_token = get_config()['mygptforbot']
# bot_token = get_config()['clsvipBot']
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 10808)
socket.socket = socks.socksocket #使用socks建立连接

bot = telebot.TeleBot(token=bot_token)
def send_to_telegram(content):
    updates = bot.get_updates()
    for update in updates:
        # 获取消息对象
        message = update.message
        chat_id=message.chat.id
        bot.send_message(chat_id=chat_id, text=content)
        # print(f'message:{message}')
        text=message.text
        return text

    bot.polling()
# def delete_webhook(token):
#     url = f'https://api.telegram.org/bot{token}/deleteWebhook'
#     response = requests.post(url)
#     return response.json()

if __name__ == '__main__':
    # 测试发送消息
    print(send_to_telegram("使用python3 向telegram 发送通知"))
    # result=delete_webhook(bot_token)
    # print(result)