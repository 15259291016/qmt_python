'''
Date: 2024-08-27 13:50:41
LastEditors: 牛智超
LastEditTime: 2024-08-27 15:38:39
FilePath: \国金项目\algo\在网上找的代码\设计模式\结构型模式\装饰器模式\main.py
'''
# 抽象组件
from abc import ABC, abstractmethod

class Message(ABC):
    @abstractmethod
    def get_message(self):
        pass
    
# 具体组件
class PlainTextMessage(Message):
    def __init__(self, message):
        self.message = message

    def get_message(self):
        return self.message
    
# 抽象装饰器
class MessageDecorator(Message):
    def __init__(self, message):
        self._message = message
        
# 具体装饰器
class BoldMessageDecorator(MessageDecorator):
    def get_message(self):
        return f"<b>{self._message.get_message()}</b>"

class ItalicMessageDecorator(MessageDecorator):
    def get_message(self):
        return f"<i>{self._message.get_message()}</i>"

class UnderlineMessageDecorator(MessageDecorator):
    def get_message(self):
        return f"<u>{self._message.get_message()}</u>"
    
# 使用装饰器模式
def main():
    # 创建一个基础的消息对象
    base_message = PlainTextMessage("Hello, world!")
    print(f"Original message: {base_message.get_message()}")

    # 使用装饰器动态地添加格式
    bold_message = BoldMessageDecorator(base_message)
    print(f"BOLD: {bold_message.get_message()}")

    italic_message = ItalicMessageDecorator(base_message)
    print(f"ITALIC: {italic_message.get_message()}")

    underline_message = UnderlineMessageDecorator(base_message)
    print(f"UNDERLINE: {underline_message.get_message()}")

    # 组合装饰器
    combined_message = BoldMessageDecorator(ItalicMessageDecorator(UnderlineMessageDecorator(base_message)))
    print(f"COMBINED: {combined_message.get_message()}")

if __name__ == "__main__":
    main()