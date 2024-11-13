'''
Date: 2024-08-27 09:54:26
LastEditors: 牛智超
LastEditTime: 2024-08-27 09:54:36
FilePath: \设计模式\抽象工厂模式\main.py
'''
# AbstractButton 和 AbstractTextField 是抽象产品接口。
# WindowsButton, MacButton, WindowsTextField, MacTextField 是具体产品。
# AbstractGUIFactory 是抽象工厂接口，声明了创建不同产品的方法。
# WindowsFactory 和 MacFactory 是具体工厂，它们实现了抽象工厂接口，并创建了对应平台的具体产品。

from abc import ABC, abstractmethod


# 抽象产品
class AbstractButton(ABC):
    @abstractmethod
    def paint(self) -> str:
        pass

class AbstractTextField(ABC):
    @abstractmethod
    def paint(self) -> str:
        pass


# 具体产品
class WindowsButton(AbstractButton):
    def paint(self) -> str:
        return "WindowsButton: Draw button in Windows style."

class MacButton(AbstractButton):
    def paint(self) -> str:
        return "MacButton: Draw button in Mac style."

class WindowsTextField(AbstractTextField):
    def paint(self) -> str:
        return "WindowsTextField: Draw text field in Windows style."

class MacTextField(AbstractTextField):
    def paint(self) -> str:
        return "MacTextField: Draw text field in Mac style."


# 抽象工厂
class AbstractGUIFactory(ABC):
    @abstractmethod
    def create_button(self) -> AbstractButton:
        pass

    @abstractmethod
    def create_text_field(self) -> AbstractTextField:
        pass


# 具体工厂
class WindowsFactory(AbstractGUIFactory):
    def create_button(self) -> AbstractButton:
        return WindowsButton()

    def create_text_field(self) -> AbstractTextField:
        return WindowsTextField()

class MacFactory(AbstractGUIFactory):
    def create_button(self) -> AbstractButton:
        return MacButton()

    def create_text_field(self) -> AbstractTextField:
        return MacTextField()


# 使用抽象工厂模式
def client_code(factory: AbstractGUIFactory) -> None:
    button = factory.create_button()
    text_field = factory.create_text_field()

    print(button.paint())
    print(text_field.paint())


if __name__ == "__main__":
    print("Client: Testing client code with the Windows GUI Factory type:")
    client_code(WindowsFactory())

    print("\n")

    print("Client: Testing the same client code with the Mac GUI Factory type:")
    client_code(MacFactory())