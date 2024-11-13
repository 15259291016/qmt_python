'''
Date: 2024-08-27 14:21:23
LastEditors: 牛智超
LastEditTime: 2024-08-27 14:23:56
FilePath: \国金项目\algo\在网上找的代码\设计模式\行为型模式\策略模式\main.py
'''
# 策略接口
from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass
# 具体策略
class CreditCardStrategy(PaymentStrategy):
    def __init__(self, card_number, card_holder, expiration_date, security_code):
        self.card_number = card_number
        self.card_holder = card_holder
        self.expiration_date = expiration_date
        self.security_code = security_code

    def pay(self, amount):
        print(f"Paying ${amount} using credit card: {self.card_number[-4:]}")

class PayPalStrategy(PaymentStrategy):
    def __init__(self, email_address, password):
        self.email_address = email_address
        self.password = password

    def pay(self, amount):
        print(f"Paying ${amount} using PayPal account: {self.email_address}")

class ApplePayStrategy(PaymentStrategy):
    def __init__(self, device_account_number, expiration_date):
        self.device_account_number = device_account_number
        self.expiration_date = expiration_date

    def pay(self, amount):
        print(f"Paying ${amount} using Apple Pay: {self.device_account_number[-4:]}")
        
# 上下文
class Order:
    def __init__(self, price):
        self.price = price

    def set_payment_strategy(self, strategy: PaymentStrategy):
        self._payment_strategy = strategy

    def pay(self):
        self._payment_strategy.pay(self.price)

# 使用策略模式
def main():
    order = Order(150)

    # 使用信用卡支付
    order.set_payment_strategy(CreditCardStrategy(
        "1234567890123456",
        "John Doe",
        "12/25",
        "123"
    ))
    order.pay()

    # 使用PayPal支付
    order.set_payment_strategy(PayPalStrategy(
        "john.doe@example.com",
        "mypassword"
    ))
    order.pay()

    # 使用Apple Pay支付
    order.set_payment_strategy(ApplePayStrategy(
        "A1234567890123456",
        "12/25"
    ))
    order.pay()

if __name__ == "__main__":
    main()