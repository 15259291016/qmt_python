'''
Date: 2024-08-27 09:09:18
LastEditors: 牛智超
LastEditTime: 2024-08-27 09:12:35
FilePath: \设计模式\工厂方法模式\main.py
'''
# 定义抽象产品接口
from abc import ABC, abstractmethod

class Product(ABC):
    @abstractmethod
    def operation(self) -> str:
        pass


# 创建具体产品
class ConcreteProductA(Product):
    def operation(self) -> str:
        return "ConcreteProductA: Here's the result on the platform A."

class ConcreteProductB(Product):
    def operation(self) -> str:
        return "ConcreteProductB: Here's the result on the platform B."

# 定义抽象工厂
class Creator(ABC):
    @abstractmethod
    def factory_method(self) -> Product:
        pass

    def some_operation(self) -> str:
        product = self.factory_method()
        result = f"Creator: The same creator's code has just worked with {product.operation()}"
        return result

# 创建具体工厂
class ConcreteCreatorA(Creator):
    def factory_method(self) -> Product:
        return ConcreteProductA()

class ConcreteCreatorB(Creator):
    def factory_method(self) -> Product:
        return ConcreteProductB()


# 使用工厂方法模式
def client_code(creator: Creator) -> None:
    print(f"Client: I'm not aware of the creator's class, but it still works.\n"
          f"{creator.some_operation()}", end="")

if __name__ == "__main__":
    print("App: Launched with the ConcreteCreatorA.")
    client_code(ConcreteCreatorA())
    print("\n")

    print("App: Launched with the ConcreteCreatorB.")
    client_code(ConcreteCreatorB())